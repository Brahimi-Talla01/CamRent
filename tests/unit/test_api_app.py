"""Tests de l'application publique : route de santé et format unique des erreurs.

Les erreurs sont testées par des routes montées dans le test lui-même (aucune route
métier n'existe encore dans le socle #50) : c'est le gestionnaire d'erreurs réel qui
est exercé, pas une copie.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.infrastructure import config
from backend.schemas.prediction import PredictionRequest

VALID_PAYLOAD = {
    "city": "Douala",
    "neighborhood": "Bonamoussadi",
    "property_type": "apartment",
    "bedrooms": 2,
    "bathrooms": 2,
}


def _client(app: FastAPI) -> TestClient:
    """Client de test qui ne relance pas l'exception : on teste la réponse d'erreur."""
    return TestClient(app, raise_server_exceptions=False)


def test_health_route_returns_contract_version() -> None:
    response = _client(create_app()).get(f"{config.API_PREFIX}/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_version"] == config.API_VERSION
    assert body["api_prefix"] == "/api/v1"


def test_health_route_is_not_served_without_prefix() -> None:
    """Le contrat est versionné : la route n'existe pas hors `/api/v1`."""
    assert _client(create_app()).get("/health").status_code == 404


def test_unknown_path_uses_the_single_error_shape() -> None:
    response = _client(create_app()).get(f"{config.API_PREFIX}/inconnu")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["details"] == []


def test_validation_error_lists_each_refused_field() -> None:
    """Le refus d'entrée porte le détail par champ, au format unique."""
    app = create_app()

    @app.post(f"{config.API_PREFIX}/echo")
    async def echo(payload: PredictionRequest) -> dict[str, str]:
        return {"city": payload.city}

    response = _client(app).post(
        f"{config.API_PREFIX}/echo", json={**VALID_PAYLOAD, "area_m2": 80, "bedrooms": 42}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Entrée invalide."
    assert sorted(detail["field"] for detail in body["error"]["details"]) == [
        "area_m2",
        "bedrooms",
    ]


def test_valid_payload_reaches_the_route() -> None:
    """Contrôle positif : sans lui, un 422 systématique passerait pour un succès."""
    app = create_app()

    @app.post(f"{config.API_PREFIX}/echo")
    async def echo(payload: PredictionRequest) -> dict[str, str]:
        return {"city": payload.city}

    response = _client(app).post(f"{config.API_PREFIX}/echo", json=VALID_PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {"city": "Douala"}


def test_wrong_method_uses_the_single_error_shape() -> None:
    response = _client(create_app()).post(f"{config.API_PREFIX}/health", json={})

    assert response.status_code == 405
    assert response.json()["error"]["message"]


def test_internal_failure_does_not_leak_technical_detail() -> None:
    """Un échec interne est générique : aucun message technique ne sort de l'API."""
    app = create_app()

    @app.get("/echec")
    async def fail() -> None:
        raise RuntimeError("mot de passe=change-me")

    response = _client(app).get("/echec")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "change-me" not in response.text
    assert "RuntimeError" not in response.text
