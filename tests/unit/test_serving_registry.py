"""Test d'intégration du serving contre un **vrai** registre MLflow (SQLite).

Le chemin de production est exercé ici sans le poste de développement : le
registre est une base SQLite temporaire et les artefacts vivent dans un
répertoire temporaire. Le pin est écrit comme le ferait la CLI de promotion, puis
le `PinnedModelProvider` charge **le modèle et l'intervalle** depuis le run
épinglé — exactement ce que fait l'API en production.

Ce test est le pendant CI de la vérification HTTP réelle : il ne dépend ni d'une
base PostgreSQL, ni des artefact d'une machine (ticket #52, limite « chargement
réel testé en local seulement »).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import joblib
import pytest

mlflow = pytest.importorskip("mlflow")
from mlflow import MlflowClient  # noqa: E402
from serving_fixture import build_bundle  # noqa: E402

from backend.ml import loader  # noqa: E402
from backend.ml.loader import PinnedModelProvider, ServingError  # noqa: E402
from backend.ml.service import EstimationService  # noqa: E402
from backend.schemas.prediction import PredictionRequest  # noqa: E402
from ml.src import config as ml_config  # noqa: E402

REQUEST = PredictionRequest(
    city="Douala",
    neighborhood="Makepe",
    property_type="apartment",
    bedrooms=2,
    bathrooms=2,
)


@pytest.fixture()
def registry(tmp_path: Path, mlflow_sqlite_uri: str, monkeypatch: pytest.MonkeyPatch):
    """Registre SQLite isolé + pin écrit hors dépôt, comme en production."""
    previous_uri = mlflow.get_tracking_uri()
    monkeypatch.setenv("MLFLOW_TRACKING_URI", mlflow_sqlite_uri)
    monkeypatch.setattr(ml_config, "MLFLOW_TRACKING_URI", mlflow_sqlite_uri)
    mlflow.set_tracking_uri(mlflow_sqlite_uri)
    client = MlflowClient()
    # Nom unique : la base SQLite est partagée par toute la session de tests.
    experiment_id = client.create_experiment(
        f"serving_fixture_{uuid.uuid4().hex[:8]}",
        artifact_location=(tmp_path / "artifacts").as_uri(),
    )
    yield {"client": client, "experiment_id": experiment_id, "directory": tmp_path}
    mlflow.set_tracking_uri(previous_uri)


def _register(
    registry: dict, *, log_interval: bool = True, pin_name: str = "champion.json"
) -> tuple[Path, dict[str, object]]:
    """Journalise le modèle (et l'intervalle) puis épingle la version promue."""
    bundle = build_bundle()
    interval_file = registry["directory"] / loader.interval_artifact_name()
    joblib.dump(bundle.interval, interval_file)
    with mlflow.start_run(
        experiment_id=registry["experiment_id"], run_name="serving-fixture"
    ) as run:
        info = mlflow.sklearn.log_model(
            bundle.model, name="modele", serialization_format="cloudpickle"
        )
        if log_interval:
            mlflow.log_artifact(str(interval_file))
        run_id = run.info.run_id

    version = mlflow.register_model(info.model_uri, "rent-model")
    client = registry["client"]
    client.set_registered_model_alias("rent-model", "champion", version.version)
    source = client.get_model_version("rent-model", str(version.version)).source
    pin = {
        "pin_version": 1,
        "nom": "rent-model",
        "version": int(version.version),
        "etiquette": f"rent-model-v{version.version}",
        "alias": "champion",
        "run_id": run_id,
        "model_uri": source,
        "dataset": {
            "source": "analytics_marts.mart_ml_dataset",
            "version": "mart_ml_dataset@fixture",
            "hash_md5": "0" * 32,
            "n_observations": 24,
        },
    }
    pin_path = registry["directory"] / pin_name
    pin_path.write_text(json.dumps(pin), encoding="utf-8")
    return pin_path, pin


def test_serving_loads_model_and_interval_from_the_pinned_run(registry: dict) -> None:
    """Modèle **et** intervalle viennent du run épinglé : le serving est complet."""
    pin_path, pin = _register(registry)

    loader.verify_pinned_version(pin)
    provider = PinnedModelProvider(pin_path=pin_path)
    response = EstimationService(provider).estimate(REQUEST)

    assert response.model_version == pin["etiquette"]
    assert response.lower_bound <= response.estimated_rent <= response.upper_bound


def test_model_version_is_the_pinned_one_not_the_registry_latest(registry: dict) -> None:
    """Une version plus récente n'est pas servie : seul le pin fait foi."""
    pin_path, pin = _register(registry)
    # Nouvelle version + alias déplacé : le pin existant devient périmé.
    _register(registry, pin_name="champion-perime.json")

    provider = PinnedModelProvider(pin_path=pin_path)
    with pytest.raises(ServingError, match="Provenance incohérente"):
        provider.load()


def test_interval_missing_from_the_pinned_run_is_an_explicit_error(registry: dict) -> None:
    """Sans artefact d'intervalle dans le run épinglé, rien n'est servi."""
    pin_path, pin = _register(registry, log_interval=False)

    with pytest.raises(ServingError, match="absent du run épinglé"):
        loader.load_interval(pin)

    # Le pin reste lisible : c'est l'artefact qui manque, pas la provenance.
    assert loader.read_champion_pin(pin_path)["run_id"] == pin["run_id"]
