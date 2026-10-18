"""Tests du chargement du modèle épinglé et du service d'estimation (ticket #51).

Le modèle servi est le **fixture isolé** `serving_fixture` : un pipeline
scikit-learn minimal entraîné dans le test — ni registre MLflow, ni artefact du
poste local, ni base, donc ces tests passent en CI sur une machine neuve.
La provenance est vérifiée séparément, avec un client de registre factice : le
alias de référence doit pointer la version et l'artefact épinglés.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from serving_fixture import (
    MODEL_VERSION,
    NEIGHBORHOODS,
    build_bundle,
    pin_payload,
    write_pin,
)

from backend.ml import loader, service
from backend.ml.loader import PinnedModelProvider, ServingBundle, ServingError
from backend.schemas.prediction import PredictionRequest

VALID_REQUEST = PredictionRequest(
    city="Douala",
    neighborhood="Makepe",
    property_type="apartment",
    bedrooms=2,
    bathrooms=2,
)


@pytest.fixture()
def bundle() -> ServingBundle:
    """Bundle de test (pipeline minimal + intervalle calibré)."""
    return build_bundle()


@pytest.fixture()
def pin_path(tmp_path: Path) -> Path:
    """Pin de test écrit hors dépôt (répertoire temporaire)."""
    return write_pin(tmp_path)


@pytest.fixture()
def provider(pin_path: Path, bundle: ServingBundle) -> PinnedModelProvider:
    """Provider servi par les tests : chargeurs injectés, pin réel de test."""
    return PinnedModelProvider(
        pin_path=pin_path,
        model_loader=lambda pin: bundle.model,
        interval_loader=lambda pin: bundle.interval,
    )


def test_default_paths_point_to_the_pinned_artifacts() -> None:
    """Le pin est versionné ; l'intervalle est un artefact du run épinglé."""
    assert loader.champion_pin_path().name == "champion.json"
    assert loader.interval_artifact_name() == "rent_model_v1_intervalle.joblib"


def test_missing_pin_is_an_explicit_error(tmp_path: Path) -> None:
    missing = tmp_path / "champion.json"

    with pytest.raises(ServingError) as exc_info:
        loader.read_champion_pin(missing)

    assert "Version épinglée introuvable" in str(exc_info.value)
    assert str(missing) in str(exc_info.value)


def test_unreadable_pin_is_an_explicit_error(tmp_path: Path) -> None:
    pin = tmp_path / "champion.json"
    pin.write_text("{pas du json", encoding="utf-8")

    with pytest.raises(ServingError, match="illisible"):
        loader.read_champion_pin(pin)


def test_incomplete_pin_is_an_explicit_error(tmp_path: Path) -> None:
    pin = tmp_path / "champion.json"
    pin.write_text(json.dumps({"etiquette": "rent-model-v3"}), encoding="utf-8")

    with pytest.raises(ServingError) as exc_info:
        loader.read_champion_pin(pin)

    assert "incomplète" in str(exc_info.value)
    assert "model_uri" in str(exc_info.value)


def test_pin_without_dataset_provenance_is_refused(tmp_path: Path) -> None:
    """Servir sans provenance de données rendrait la version invérifiable."""
    payload = pin_payload()
    payload["dataset"] = {"source": "analytics_marts.mart_ml_dataset"}
    pin = tmp_path / "champion.json"
    pin.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ServingError) as exc_info:
        loader.read_champion_pin(pin)

    assert "Provenance du pin incomplète" in str(exc_info.value)
    assert "dataset.hash_md5" in str(exc_info.value)


class _FakeRegistry:
    """Registre minimal : l'alias de référence pointe la version attendue."""

    def __init__(self, *, version: int, source: str) -> None:
        self.version = version
        self.source = source
        self.missing = False

    def get_model_version_by_alias(self, name: str, alias: str) -> object:
        if self.missing:
            raise LookupError(f"alias {alias} introuvable pour {name}")

        class _Version:
            pass

        version = _Version()
        version.version = self.version
        version.source = self.source
        return version


def test_provenance_check_accepts_the_pinned_version() -> None:
    payload = pin_payload()
    client = _FakeRegistry(version=payload["version"], source=str(payload["model_uri"]))

    loader.verify_pinned_version(payload, client=client)


def test_provenance_check_refuses_a_moved_alias() -> None:
    """Un alias déplacé à la main ne doit jamais être servi en silence."""
    payload = pin_payload()
    client = _FakeRegistry(version=99, source="models:/m-autre")

    with pytest.raises(ServingError, match="Provenance incohérente"):
        loader.verify_pinned_version(payload, client=client)


def test_provenance_check_refuses_a_missing_alias() -> None:
    client = _FakeRegistry(version=1, source=str(pin_payload()["model_uri"]))
    client.missing = True

    with pytest.raises(ServingError, match="provenance du modèle servi non vérifiable"):
        loader.verify_pinned_version(pin_payload(), client=client)


def test_missing_interval_is_an_explicit_error(tmp_path: Path) -> None:
    """Sans fourchette calibrée, rien n'est servi (jamais de fourchette improvisée)."""
    with pytest.raises(ServingError) as exc_info:
        loader.load_interval(path=tmp_path / "rent_model_v1_intervalle.joblib")

    assert "Intervalle de prédiction introuvable" in str(exc_info.value)


def test_pin_without_run_id_cannot_locate_the_interval() -> None:
    """L'intervalle vient du run épinglé : un pin sans `run_id` est refusé."""
    payload = pin_payload()
    payload.pop("run_id")

    with pytest.raises(ServingError, match="sans `run_id`"):
        loader.load_interval(payload)


def test_provider_loads_the_bundle_once(tmp_path: Path, bundle: ServingBundle) -> None:
    calls = {"model": 0, "interval": 0}

    def model_loader(pin: dict) -> object:
        calls["model"] += 1
        return bundle.model

    def interval_loader(pin: dict) -> object:
        calls["interval"] += 1
        return bundle.interval

    provider = PinnedModelProvider(
        pin_path=write_pin(tmp_path),
        model_loader=model_loader,
        interval_loader=interval_loader,
    )

    first = provider.load()
    second = provider.load()

    assert first is second
    assert calls == {"model": 1, "interval": 1}
    assert first.model_version == MODEL_VERSION


def test_estimate_returns_calibrated_bounds(provider: PinnedModelProvider) -> None:
    response = service.EstimationService(provider).estimate(VALID_REQUEST)

    assert response.model_version == MODEL_VERSION
    assert response.currency == "XAF"
    assert isinstance(response.estimated_rent, int)
    assert response.lower_bound <= response.estimated_rent <= response.upper_bound
    assert response.lower_bound >= 1


def test_estimate_is_reproducible(provider: PinnedModelProvider) -> None:
    estimation = service.EstimationService(provider)

    first = estimation.estimate(VALID_REQUEST).model_dump()
    second = estimation.estimate(VALID_REQUEST).model_dump()

    assert first == second


def test_every_known_pair_is_estimable(provider: PinnedModelProvider) -> None:
    estimation = service.EstimationService(provider)

    for city, neighborhoods in NEIGHBORHOODS.items():
        for neighborhood in neighborhoods:
            request = PredictionRequest(
                city=city,
                neighborhood=neighborhood,
                property_type="apartment",
                bedrooms=2,
                bathrooms=1,
            )
            response = estimation.estimate(request)
            assert response.lower_bound <= response.estimated_rent <= response.upper_bound


def test_unknown_neighborhood_is_refused(provider: PinnedModelProvider) -> None:
    request = PredictionRequest(
        city="Douala",
        neighborhood="QuartierInexistant",
        property_type="apartment",
        bedrooms=2,
        bathrooms=1,
    )

    with pytest.raises(service.UnknownNeighborhoodError) as exc_info:
        service.EstimationService(provider).estimate(request)

    assert "Quartier inconnu pour Douala" in str(exc_info.value)
    assert "QuartierInexistant" in str(exc_info.value)


def test_neighborhood_of_another_city_is_refused(provider: PinnedModelProvider) -> None:
    """Un quartier réel mais jamais vu avec cette ville n'est pas estimé."""
    request = PredictionRequest(
        city="Douala",
        neighborhood="Mvog-Ada",  # vu uniquement à Yaoundé dans le fixture
        property_type="apartment",
        bedrooms=2,
        bathrooms=1,
    )

    with pytest.raises(service.UnknownNeighborhoodError):
        service.EstimationService(provider).estimate(request)


def test_inverted_or_negative_bounds_are_floored(
    pin_path: Path, bundle: ServingBundle
) -> None:
    """L'invariant « fourchette ordonnée et positive » tient même avec un artefact absurde."""

    class _BrokenInterval:
        def bounds(self, frame: object) -> tuple[float, float]:
            return (120_000.0, -5_000.0)

    provider = PinnedModelProvider(
        pin_path=pin_path,
        model_loader=lambda pin: bundle.model,
        interval_loader=lambda pin: _BrokenInterval(),
    )

    response = service.EstimationService(provider).estimate(VALID_REQUEST)

    assert response.lower_bound == 1
    assert response.upper_bound == 120_000


def test_non_conform_model_is_refused(provider: PinnedModelProvider) -> None:
    """Un artefact sans profondeur d'entraînement ne peut pas servir (erreur explicite)."""
    broken = ServingBundle(pin={"etiquette": "x", "model_uri": "y"}, model=object(), interval=None)

    with pytest.raises(ServingError, match="non conforme"):
        service.known_city_neighborhood_pairs(broken)
