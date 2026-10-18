"""Tests de l'endpoint `POST /api/v1/predictions` (ticket #51).

L'application est montée avec le **fixture de service isolé** (`serving_fixture`)
: ni registre MLflow, ni base, ni artefact local. Le contrat est donc vérifié tel
qu'il sera exécuté en CI, et le chargement réel du modèle épinglé est contrôlé
séparément par la vérification HTTP de la phase 8 sur le poste de développement.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from serving_fixture import MODEL_VERSION, build_bundle, write_pin

from backend.api.app import create_app
from backend.api.routes import predictions as predictions_route
from backend.ml.loader import PinnedModelProvider, ServingBundle, ServingError
from backend.ml.service import EstimationService

VALID_PAYLOAD = {
    "city": "Douala",
    "neighborhood": "Makepe",
    "property_type": "apartment",
    "bedrooms": 2,
    "bathrooms": 2,
}


def _client(bundle: ServingBundle, tmp_path: Path, *, failing: bool = False) -> TestClient:
    """Client de test monté sur le fixture, avec échec de chargement simulé si demandé."""

    def model_loader(pin: dict) -> object:
        if failing:
            raise ServingError("registre MLflow injoignable (test)")
        return bundle.model

    provider = PinnedModelProvider(
        pin_path=write_pin(tmp_path),
        model_loader=model_loader,
        interval_loader=lambda pin: bundle.interval,
    )
    app = create_app()
    app.dependency_overrides[predictions_route.get_estimation_service] = lambda: (
        EstimationService(provider)
    )
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def bundle() -> ServingBundle:
    """Bundle de test (pipeline minimal + intervalle calibré)."""
    return build_bundle()


@pytest.fixture()
def client(bundle: ServingBundle, tmp_path: Path) -> TestClient:
    return _client(bundle, tmp_path)


def test_prediction_returns_the_documented_contract(client: TestClient) -> None:
    response = client.post("/api/v1/predictions", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert sorted(body) == [
        "currency",
        "estimated_rent",
        "lower_bound",
        "model_version",
        "upper_bound",
    ]
    assert body["currency"] == "XAF"
    assert body["model_version"] == MODEL_VERSION
    assert isinstance(body["estimated_rent"], int)
    assert body["lower_bound"] <= body["estimated_rent"] <= body["upper_bound"]


def test_prediction_is_reproducible(client: TestClient) -> None:
    first = client.post("/api/v1/predictions", json=VALID_PAYLOAD)
    second = client.post("/api/v1/predictions", json=VALID_PAYLOAD)

    assert first.status_code == 200
    assert first.json() == second.json()


def test_unknown_neighborhood_is_a_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/predictions", json={**VALID_PAYLOAD, "neighborhood": "QuartierInexistant"}
    )

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "QuartierInexistant" in body["error"]["message"]
    assert "estimated_rent" not in response.text


def test_non_collected_field_is_refused_by_the_route(client: TestClient) -> None:
    response = client.post("/api/v1/predictions", json={**VALID_PAYLOAD, "area_m2": 80})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_city_outside_the_vocabulary_is_refused(client: TestClient) -> None:
    response = client.post("/api/v1/predictions", json={**VALID_PAYLOAD, "city": "Lyon"})

    assert response.status_code == 422


def test_serving_failure_is_a_generic_500(bundle: ServingBundle, tmp_path: Path) -> None:
    """Un échec de chargement ne divulgue ni chemin ni détail technique (AGENTS.md §9)."""
    client = _client(bundle, tmp_path, failing=True)

    response = client.post("/api/v1/predictions", json=VALID_PAYLOAD)

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["message"] == "Erreur interne du service."
    assert "champion.json" not in response.text
    assert "ServingError" not in response.text


def test_endpoint_is_documented_in_openapi() -> None:
    paths = create_app().openapi()["paths"]

    assert "/api/v1/predictions" in paths
    assert "post" in paths["/api/v1/predictions"]
