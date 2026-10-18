"""Tests du registre de modèles et de la règle de promotion (Phase 7).

Le backend est une base SQLite temporaire : le Model Registry MLflow ne
fonctionne pas sur un file store, ce que ces tests vérifient aussi.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

mlflow = pytest.importorskip("mlflow")

from ml.src import config, registry, registry_report, tracking  # noqa: E402


def _selection(*, gain: float, beat: int, total: int, seuil: bool) -> dict[str, object]:
    return {
        "gain_vs_baseline_pct": gain,
        "mae_validation": 75_425,
        "seuil_mae_borne_basse_ic": 79_773,
        "bat_le_seuil_validation": seuil,
        "gain_median_pct": 12.35,
        "robustesse": {
            "nb_graines": total,
            "nb_graines_battant_la_baseline": beat,
        },
    }


THRESHOLD = {"baseline": "baseline_neighborhood", "mae_borne_basse_ic": 79_773}


def test_promotion_when_all_conditions_hold() -> None:
    decision = registry.promotion_decision(
        _selection(gain=22.31, beat=3, total=3, seuil=True), THRESHOLD
    )
    assert decision["promotion"] is True
    assert all(condition["satisfait"] for condition in decision["conditions"])


def test_no_promotion_when_the_baseline_is_not_beaten_everywhere() -> None:
    decision = registry.promotion_decision(
        _selection(gain=22.31, beat=2, total=3, seuil=True), THRESHOLD
    )
    conditions = {condition["id"]: condition["satisfait"] for condition in decision["conditions"]}
    assert conditions["bat_la_baseline"] is False
    assert conditions["seuil_phase_5"] is True
    assert decision["promotion"] is False


def test_no_promotion_when_neither_seed_nor_threshold_is_met() -> None:
    decision = registry.promotion_decision(
        _selection(gain=-5.0, beat=0, total=1, seuil=False), THRESHOLD
    )
    assert decision["promotion"] is False
    conditions = {condition["id"]: condition for condition in decision["conditions"]}
    assert conditions["bat_la_baseline"]["satisfait"] is False
    assert conditions["seuil_phase_5"]["satisfait"] is False
    assert conditions["reproductible"]["satisfait"] is False


def test_promotion_rule_is_documented_and_serializable() -> None:
    rule = registry.promotion_rule()
    identifiers = [condition["id"] for condition in rule["conditions"]]
    assert identifiers == ["bat_la_baseline", "seuil_phase_5", "reproductible"]
    assert "explicite" in rule["portee"]


def test_promotion_requires_an_explicit_approval() -> None:
    """Règle satisfaite ≠ promotion : l'approbation est nominative."""
    decision = registry.promotion_decision(
        _selection(gain=22.31, beat=3, total=3, seuil=True), THRESHOLD
    )
    assert decision["promotion"] is True
    with pytest.raises(ValueError, match="approbation"):
        registry.require_promotion_approval(decision)
    # Une identité explicite suffit : la fonction ne lève plus.
    registry.require_promotion_approval(decision, approved_by="admin")


def test_no_approval_is_required_when_the_rule_is_not_satisfied() -> None:
    decision = registry.promotion_decision(
        _selection(gain=-1.0, beat=0, total=1, seuil=False), THRESHOLD
    )
    assert decision["promotion"] is False
    registry.require_promotion_approval(decision)


def test_register_refuses_to_promote_without_approval(mlflow_sqlite_uri: str) -> None:
    """Aucune version n'est créée tant que la promotion n'est pas approuvée."""
    with pytest.raises(ValueError, match="approbation"):
        registry.register(
            model_uri="runs:/inexistant/modele",
            run_id="inexistant",
            metadata={
                "famille": "linéaire",
                "cible_transformee": "brut",
                "graine": 7,
                "features": [],
            },
            decision={"promotion": True},
            dataset={"version": "v", "hash_md5": "h"},
            code={"git_sha": "sha"},
        )


def test_registry_requires_a_database_backend(mlflow_sqlite_uri: str) -> None:
    previous = mlflow.get_tracking_uri()
    mlflow.set_tracking_uri("/tmp/camrent-mlruns-not-a-db")
    try:
        with pytest.raises(ValueError, match="Model Registry"):
            registry.register(
                model_uri="runs:/x/modele",
                run_id="x",
                metadata={
                    "famille": "linéaire",
                    "cible_transformee": "brut",
                    "graine": 7,
                    "features": [],
                },
                decision={"promotion": False},
                dataset={"version": "v", "hash_md5": "h"},
                code={"git_sha": "sha"},
            )
    finally:
        mlflow.set_tracking_uri(previous)


def test_register_creates_a_version_and_sets_the_alias(
    mlflow_sqlite_uri: str, ml_frame: pd.DataFrame, tmp_path
) -> None:
    results = {
        "meta": {
            "graine": 7,
            "features": ["city"],
            "proportions": {"train": 0.7, "validation": 0.15, "test": 0.15},
        },
        "candidats": {
            "alpha": {
                "slug": "alpha",
                "label": "alpha",
                "famille": "ensemble d'arbres (bagging)",
                "cible_transformee": "log1p",
                "complexite": "moyenne",
                "interpretabilite": "importance par permutation",
                "hyperparametres": {"seed": 7},
                "entrainement_s": 0.3,
                "metriques": {
                    split: {"n": 10, "mae": 1.0, "rmse": 2.0, "r2": 0.5, "medae": 1.0,
                            "p90": 2.0, "part_a_moins_de_20_pct": 50.0, "temps_prediction_s": 0.01}
                    for split in ("train", "validation", "test")
                },
            }
        },
        "selection": {"slug": "alpha"},
    }
    dataset = tracking.dataset_version(ml_frame)
    logged = tracking.log_candidate_runs(
        results, dataset=dataset, tracking_uri=mlflow_sqlite_uri, experiment="test_registry"
    )
    frame = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]})
    model = LinearRegression().fit(frame, [1.0, 2.0, 3.0, 4.0])
    metadata = {
        "nom": "rent_model_v1",
        "famille": "ensemble d'arbres (bagging)",
        "cible_transformee": "log1p",
        "graine": 7,
        "features": ["city"],
    }
    model_uri = tracking.log_retained_model(
        run_id=logged["retenu"], model=model, metadata=metadata
    )

    pin = tmp_path / "champion.json"
    registered = registry.register(
        model_uri=model_uri,
        run_id=logged["retenu"],
        metadata=metadata,
        decision={"promotion": True},
        dataset=dataset,
        code={"git_sha": "deadbeef"},
        approved_by="admin",
        pin_path=pin,
    )
    assert registered["etiquette"] == "rent-model-v1"
    assert registered["alias"] == "champion"
    assert registered["version"] == 1
    assert registered["approuve_par"] == "admin"
    assert registered["epingle"] == str(pin)

    client = mlflow.MlflowClient()
    version = client.get_model_version("rent-model", "1")
    assert version.tags["famille"] == "ensemble d'arbres (bagging)"
    assert version.tags["version_dataset"] == dataset["version"]
    assert version.tags["promu"] == "True"
    assert version.tags["approuve_par"] == "admin"
    assert version.tags["approuve_le"] != ""
    assert client.get_model_version_by_alias("rent-model", "champion").version == 1

    # La version servie est épinglée dans un fichier versionné, sans secret.
    pinned = registry.read_champion_pin(pin)
    assert pinned["version"] == 1
    assert pinned["etiquette"] == "rent-model-v1"
    assert pinned["alias"] == "champion"
    assert pinned["run_id"] == logged["retenu"]
    assert pinned["approuve_par"] == "admin"
    assert pinned["git_sha"] == "deadbeef"
    assert pinned["dataset"]["hash_md5"] == dataset["hash_md5"]
    assert "mot-de-passe" not in pin.read_text(encoding="utf-8")


def test_read_champion_pin_raises_when_the_file_is_missing(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="introuvable"):
        registry.read_champion_pin(tmp_path / "absent.json")


def test_read_champion_pin_refuses_an_unreadable_file(tmp_path) -> None:
    """Un pin illisible ne doit jamais être interprété comme « pas de pin »."""
    pin = tmp_path / "champion.json"
    pin.write_text("{pas du json", encoding="utf-8")

    with pytest.raises(ValueError, match="illisible"):
        registry.read_champion_pin(pin)


def test_read_champion_pin_refuses_an_incomplete_pin(tmp_path) -> None:
    pin = tmp_path / "champion.json"
    pin.write_text(json.dumps({"etiquette": "rent-model-v4"}), encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        registry.read_champion_pin(pin)

    assert "incomplète" in str(exc_info.value)
    assert "model_uri" in str(exc_info.value)


def test_read_champion_pin_refuses_a_pin_without_dataset_provenance(tmp_path) -> None:
    """Une version servie sans provenance de données n'est pas traçable."""
    pin = tmp_path / "champion.json"
    pin.write_text(
        json.dumps(
            {
                "nom": "rent-model",
                "version": 4,
                "etiquette": "rent-model-v4",
                "model_uri": "models:/m-1",
                "dataset": {"source": "analytics_marts.mart_ml_dataset"},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        registry.read_champion_pin(pin)

    assert "dataset.hash_md5" in str(exc_info.value)
    assert "dataset.version" in str(exc_info.value)


def test_pin_command_fails_when_the_pin_is_missing(tmp_path, capsys) -> None:
    """Contrôle avant serving : pin absent → message explicite et exit non nul."""
    from ml.src.__main__ import main

    assert main(["pin", "--pin", str(tmp_path / "absent.json")]) == 1
    assert "introuvable" in capsys.readouterr().err


def test_pin_command_prints_the_pinned_provenance(tmp_path, capsys) -> None:
    pin = tmp_path / "champion.json"
    pin.write_text(
        json.dumps(
            {
                "nom": "rent-model",
                "version": 4,
                "etiquette": "rent-model-v4",
                "model_uri": "models:/m-1",
                "dataset": {
                    "source": "analytics_marts.mart_ml_dataset",
                    "version": "mart_ml_dataset@d3c11c225f48",
                    "hash_md5": "d3c11c225f48abc36a99037d9b9f2ce9",
                },
            }
        ),
        encoding="utf-8",
    )

    from ml.src.__main__ import main

    assert main(["pin", "--pin", str(pin)]) == 0
    captured = capsys.readouterr().out
    assert "rent-model-v4" in captured
    assert "mart_ml_dataset@d3c11c225f48" in captured


def test_report_never_shows_an_absolute_path() -> None:
    """Le rapport est versionné : un chemin absolu le rendrait non reproductible."""
    assert registry_report.display_path(str(config.CHAMPION_PIN_PATH)) == (
        "ml/models/champion.json"
    )
    assert registry_report.display_path("ml/models/champion.json") == "ml/models/champion.json"
    assert registry_report.display_path("/tmp/ailleurs/champion.json") == "champion.json"
