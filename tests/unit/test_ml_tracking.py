"""Tests du suivi MLflow (Phase 7).

Aucun serveur MLflow n'est requis : les tests utilisent une base SQLite
temporaire (`sqlite:///…`), qui sert à la fois de store de suivi et de backend au
Model Registry.
"""

from __future__ import annotations

import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

mlflow = pytest.importorskip("mlflow")

from ml.src import config, tracking  # noqa: E402

SPLIT_METRICS = {
    "n": 10,
    "mae": 12.0,
    "rmse": 20.0,
    "r2": 0.5,
    "medae": 9.0,
    "erreur_absolue_p90": 30.0,
    "prix_moyen_observe": 90.0,
    "temps_prediction_s": 0.01,
}


def _candidate(slug: str, *, famille: str = "test") -> dict[str, object]:
    return {
        "slug": slug,
        "label": slug,
        "famille": famille,
        "cible_transformee": "brut",
        "complexite": "faible",
        "interpretabilite": "bonne",
        "hyperparametres": {"alpha": 1.0, "seed": 7},
        "entrainement_s": 0.5,
        "metriques": {
            "train": dict(SPLIT_METRICS),
            "validation": dict(SPLIT_METRICS),
            "test": dict(SPLIT_METRICS),
        },
        "segments_validation": {
            "ville": [
                {"ville": "Douala", "n": 8, "mae": 10.0, "sous_seuil_de_publication": False},
                {"ville": "Yaoundé", "n": 2, "mae": 22.0, "sous_seuil_de_publication": True},
            ]
        },
    }


def _fake_results(slugs: list[str]) -> dict[str, object]:
    return {
        "meta": {
            "graine": 7,
            "features": ["city", "bedrooms"],
            "proportions": {"train": 0.7, "validation": 0.15, "test": 0.15},
        },
        "candidats": {slug: _candidate(slug) for slug in slugs},
        "selection": {"slug": slugs[0]},
    }


def test_resolve_prefers_the_explicit_argument() -> None:
    assert tracking.resolve_tracking_uri("sqlite:///explicit.db") == "sqlite:///explicit.db"


def test_resolve_derives_a_dedicated_postgres_database(monkeypatch) -> None:
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://camrent:change-me@localhost:5433/camrent")
    uri = tracking.resolve_tracking_uri()
    assert uri.startswith("postgresql+psycopg://")
    assert uri.endswith("/mlflow")
    # Régression : `str(URL)` masquait le mot de passe en `***` — le vrai doit
    # être conservé, sinon l'authentification échoue.
    assert "change-me" in uri
    assert "***" not in uri
    assert tracking.mask_tracking_uri(uri).endswith("/mlflow")
    assert "***" in tracking.mask_tracking_uri(uri)


def test_resolve_falls_back_to_a_local_directory(monkeypatch) -> None:
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert tracking.resolve_tracking_uri() == str(config.MLFLOW_LOCAL_DIR)


def test_dataset_version_is_order_independent(ml_frame: pd.DataFrame) -> None:
    shuffled = ml_frame.sample(frac=1, random_state=1)
    assert tracking.dataset_version(ml_frame)["hash_md5"] == tracking.dataset_version(shuffled)[
        "hash_md5"
    ]
    version = tracking.dataset_version(ml_frame)
    assert version["n_observations"] == len(ml_frame)
    assert version["version"].startswith(config.SOURCE_TABLE)


def test_dataset_version_changes_when_the_target_changes(ml_frame: pd.DataFrame) -> None:
    modified = ml_frame.copy()
    modified.loc[0, config.TARGET] = float(modified.loc[0, config.TARGET]) + 1.0
    assert (
        tracking.dataset_version(modified)["hash_md5"]
        != tracking.dataset_version(ml_frame)["hash_md5"]
    )


def test_dataset_version_changes_when_a_feature_changes(ml_frame: pd.DataFrame) -> None:
    """Régression : le hash ne couvrait que `listing_key` et la cible.

    Une feature modifiée donnait donc la même version de dataset, ce qui faisait
    passer un run pour reproductible alors que ses données d'entrée avaient changé.
    """
    modified = ml_frame.copy()
    modified.loc[0, "bedrooms"] = int(modified.loc[0, "bedrooms"]) + 1
    assert (
        tracking.dataset_version(modified)["hash_md5"]
        != tracking.dataset_version(ml_frame)["hash_md5"]
    )


def test_dataset_version_covers_the_schema(ml_frame: pd.DataFrame) -> None:
    """Ajouter une colonne change la version (schéma inclus dans le hash)."""
    with_column = ml_frame.assign(rent_semantics="asking_rent")
    version = tracking.dataset_version(with_column)
    assert version["n_colonnes"] == len(ml_frame.columns) + 1
    assert "rent_semantics" in version["colonnes"]
    assert version["hash_md5"] != tracking.dataset_version(ml_frame)["hash_md5"]


def test_code_version_reports_git_and_software() -> None:
    code = tracking.code_version()
    assert {"git_sha", "git_branch", "git_dirty", "logiciel"} <= set(code)
    assert {"python", "pandas", "numpy", "scikit_learn"} <= set(code["logiciel"])


def test_log_candidate_runs_writes_one_run_per_candidate(
    mlflow_sqlite_uri: str, ml_frame: pd.DataFrame
) -> None:
    results = _fake_results(["alpha", "beta"])
    dataset = tracking.dataset_version(ml_frame)
    logged = tracking.log_candidate_runs(
        results, dataset=dataset, tracking_uri=mlflow_sqlite_uri, experiment="test_exp"
    )
    assert logged["runs"] == {"alpha": logged["runs"]["alpha"], "beta": logged["runs"]["beta"]}
    assert logged["retenu"] == logged["runs"]["alpha"]

    client = mlflow.MlflowClient()
    runs = client.search_runs([logged["experiment_id"]])
    assert {run.data.tags["slug"] for run in runs} == {"alpha", "beta"}
    first = next(run for run in runs if run.data.tags["slug"] == "alpha")
    assert first.data.tags["retenu"] == "True"
    assert first.data.tags["version_dataset"] == dataset["version"]
    assert first.data.metrics["mae_validation"] == 12.0
    assert first.data.params["graine"] == "7"
    # métriques par segment (spec : journalisées par run)
    assert first.data.metrics["erreur_absolue_p90_validation"] == 30.0
    assert first.data.metrics["prix_moyen_observe_validation"] == 90.0
    segments = mlflow.artifacts.load_dict(
        first.info.artifact_uri.rstrip("/") + "/segments_validation.json"
    )
    assert segments["validation"]["ville"][0]["ville"] == "Douala"


def test_log_retained_model_attaches_a_loadable_model(
    mlflow_sqlite_uri: str, ml_frame: pd.DataFrame
) -> None:
    results = _fake_results(["alpha", "beta"])
    logged = tracking.log_candidate_runs(
        results,
        dataset=tracking.dataset_version(ml_frame),
        tracking_uri=mlflow_sqlite_uri,
        experiment="test_exp_model",
    )
    frame = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [2.0, 4.0, 6.0, 8.0]})
    model = LinearRegression().fit(frame, [1.0, 2.0, 3.0, 4.0])
    model_uri = tracking.log_retained_model(
        run_id=logged["retenu"],
        model=model,
        metadata={"nom": "test", "famille": "linéaire"},
    )
    loaded = mlflow.sklearn.load_model(model_uri)
    assert loaded.predict(frame).shape == (4,)
