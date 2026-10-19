"""Tests de `POST /api/v1/comparisons` (ticket #54).

Le modèle servi est le fixture isolé (même chemin qu'en CI), le dépôt de marché
est simulé et **filtre réellement** les groupes. Les tests vérifient trois
propriétés centrales :

- la comparaison réutilise exactement `/predictions` et `/market/prices` ;
- la médiane sous le seuil n'est jamais publiée ni utilisée pour un écart ;
- un groupe de marché absent reste explicite (`market: null`), sans invention.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from market_fixture import FakeMarketRepository
from serving_fixture import MODEL_VERSION, build_bundle, write_pin

from backend.api.app import create_app
from backend.api.routes import market as market_route
from backend.api.routes import predictions as predictions_route
from backend.infrastructure import config
from backend.ml.loader import PinnedModelProvider, ServingBundle
from backend.ml.service import EstimationService
from backend.services.market import MarketService

LISTING = {
    "city": "Douala",
    "neighborhood": "Makepe",
    "property_type": "apartment",
    "bedrooms": 2,
    "bathrooms": 2,
}
PAYLOAD = {**LISTING, "asking_rent": 150_000}


@pytest.fixture()
def bundle() -> ServingBundle:
    return build_bundle()


@pytest.fixture()
def repository() -> FakeMarketRepository:
    return FakeMarketRepository()


@pytest.fixture()
def client(
    bundle: ServingBundle, repository: FakeMarketRepository, tmp_path: Path
) -> TestClient:
    """Application réelle, modèle fixture et marché simulé partagé entre les routes."""
    provider = PinnedModelProvider(
        pin_path=write_pin(tmp_path),
        model_loader=lambda pin: bundle.model,
        interval_loader=lambda pin: bundle.interval,
    )
    estimation = EstimationService(provider)
    market = MarketService(repository)
    app = create_app()
    app.dependency_overrides[predictions_route.get_estimation_service] = lambda: estimation
    app.dependency_overrides[market_route.get_market_service] = lambda: market
    return TestClient(app, raise_server_exceptions=False)


def _compare(client: TestClient, *listings: dict[str, object]) -> dict[str, object]:
    response = client.post(
        f"{config.API_PREFIX}/comparisons", json={"listings": list(listings)}
    )
    assert response.status_code == 200, response.text
    return response.json()


def _prediction(client: TestClient, listing: dict[str, object]) -> dict[str, object]:
    response = client.post(f"{config.API_PREFIX}/predictions", json=listing)
    assert response.status_code == 200, response.text
    return response.json()


def _market_group(client: TestClient, listing: dict[str, object]) -> dict[str, object]:
    response = client.get(
        f"{config.API_PREFIX}/market/prices",
        params={
            "city": listing["city"],
            "neighborhood": listing["neighborhood"],
            "property_type": listing["property_type"],
            "bedrooms": listing["bedrooms"],
        },
    )
    assert response.status_code == 200, response.text
    groups = response.json()["groups"]
    assert len(groups) == 1
    return groups[0]


def test_comparison_reuses_prediction_and_market_exactly(client: TestClient) -> None:
    body = _compare(client, PAYLOAD)
    prediction = _prediction(client, LISTING)
    group = _market_group(client, LISTING)

    assert body["currency"] == "XAF"
    assert body["min_publish_n"] == 30
    assert body["model_version"] == prediction["model_version"] == MODEL_VERSION
    assert len(body["comparisons"]) == 1

    item = body["comparisons"][0]
    assert item["listing"] == PAYLOAD
    assert item["estimate"] == {
        "estimated_rent": prediction["estimated_rent"],
        "lower_bound": prediction["lower_bound"],
        "upper_bound": prediction["upper_bound"],
    }

    market = item["market"]
    assert market["city"] == group["city"]
    assert market["neighborhood"] == group["neighborhood"]
    assert market["property_type"] == group["property_type"]
    assert market["bedrooms"] == group["bedrooms"]
    assert market["n_observations"] == group["stats"]["n_observations"]
    assert market["mean_rent_price"] == group["stats"]["mean_rent_price"]
    assert market["median_rent_price"] == group["stats"]["median_rent_price"]
    assert market["median_published"] == group["stats"]["median_published"]
    assert market["quality"] == group["quality"]

    gap = item["gaps"]["to_estimate"]
    assert gap["absolute"] == PAYLOAD["asking_rent"] - prediction["estimated_rent"]
    assert gap["relative_pct"] == round(
        100 * (PAYLOAD["asking_rent"] - prediction["estimated_rent"])
        / prediction["estimated_rent"],
        1,
    )
    assert item["gaps"]["to_market_mean"]["absolute"] == (
        PAYLOAD["asking_rent"] - group["stats"]["mean_rent_price"]
    )
    assert item["gaps"]["to_market_median"]["absolute"] == (
        PAYLOAD["asking_rent"] - group["stats"]["median_rent_price"]
    )


def test_comparison_is_reproducible(client: TestClient) -> None:
    assert _compare(client, PAYLOAD) == _compare(client, PAYLOAD)


def test_gap_is_signed(client: TestClient) -> None:
    below = _compare(client, {**PAYLOAD, "asking_rent": 50_000})
    estimate = _prediction(client, LISTING)["estimated_rent"]

    gap = below["comparisons"][0]["gaps"]["to_estimate"]
    assert gap["absolute"] == 50_000 - estimate
    assert gap["absolute"] < 0
    assert gap["relative_pct"] < 0


def test_median_under_threshold_is_not_published_nor_used(client: TestClient) -> None:
    """Le groupe à 5 observations n'a ni médiane publiée ni écart médian."""
    body = _compare(client, {**LISTING, "bedrooms": 1, "asking_rent": 80_000})
    market = body["comparisons"][0]["market"]

    assert market["n_observations"] == 5
    assert market["mean_rent_price"] == 100_000
    assert market["median_rent_price"] is None
    assert market["median_published"] is False
    assert body["comparisons"][0]["gaps"]["to_market_median"] is None
    assert body["comparisons"][0]["gaps"]["to_market_mean"] is not None


def test_absent_market_group_is_explicit(client: TestClient) -> None:
    body = _compare(client, {**LISTING, "bedrooms": 3, "asking_rent": 150_000})
    item = body["comparisons"][0]

    assert item["market"] is None
    assert item["gaps"]["to_market_mean"] is None
    assert item["gaps"]["to_market_median"] is None
    assert item["gaps"]["to_estimate"] is not None
    assert item["estimate"]["estimated_rent"] > 0


def test_multiple_listings_keep_order_and_model_version(client: TestClient) -> None:
    listing_one = {**PAYLOAD, "bedrooms": 2, "asking_rent": 150_000}
    listing_two = {**PAYLOAD, "bedrooms": 1, "bathrooms": 1, "asking_rent": 80_000}

    body = _compare(client, listing_one, listing_two)

    assert body["model_version"] == MODEL_VERSION
    assert [item["listing"]["bedrooms"] for item in body["comparisons"]] == [2, 1]
    assert [item["market"]["n_observations"] for item in body["comparisons"]] == [80, 5]
    assert [item["market"]["median_published"] for item in body["comparisons"]] == [
        True,
        False,
    ]


def test_unknown_neighborhood_is_a_404(client: TestClient) -> None:
    response = client.post(
        f"{config.API_PREFIX}/comparisons",
        json={"listings": [{**PAYLOAD, "neighborhood": "QuartierInexistant"}]},
    )

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert "QuartierInexistant" in body["error"]["message"]
    assert "estimated_rent" not in response.text


def test_empty_list_is_refused(client: TestClient) -> None:
    response = client.post(f"{config.API_PREFIX}/comparisons", json={"listings": []})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_list_size_is_bounded(client: TestClient) -> None:
    response = client.post(
        f"{config.API_PREFIX}/comparisons",
        json={"listings": [PAYLOAD] * 11},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_asking_rent_must_be_positive(client: TestClient) -> None:
    response = client.post(
        f"{config.API_PREFIX}/comparisons",
        json={"listings": [{**PAYLOAD, "asking_rent": 0}]},
    )

    assert response.status_code == 422


def test_non_collected_field_is_refused(client: TestClient) -> None:
    response = client.post(
        f"{config.API_PREFIX}/comparisons",
        json={"listings": [{**PAYLOAD, "area_m2": 80}]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_room_bounds_apply_to_comparison(client: TestClient) -> None:
    response = client.post(
        f"{config.API_PREFIX}/comparisons",
        json={"listings": [{**PAYLOAD, "bathrooms": 11}]},
    )

    assert response.status_code == 422


def test_city_outside_vocabulary_is_refused(client: TestClient) -> None:
    response = client.post(
        f"{config.API_PREFIX}/comparisons",
        json={"listings": [{**PAYLOAD, "city": "Lyon"}]},
    )

    assert response.status_code == 422


def test_endpoint_is_documented_in_openapi() -> None:
    paths = create_app().openapi()["paths"]

    assert "/api/v1/comparisons" in paths
    assert "post" in paths["/api/v1/comparisons"]
