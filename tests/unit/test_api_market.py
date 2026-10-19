"""Tests des endpoints de marché (ticket #53).

Le dépôt est simulé : ces tests vérifient le contrat HTTP, les filtres, le seuil
de publication et la forme des réponses, sans dépendre d'une base. La
comparaison aux marts réels est faite par `tests/integration/test_market_api.py`.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.api.app import create_app
from backend.api.routes.market import get_market_service
from backend.domain.market import (
    CityMarket,
    MarketQuality,
    MarketStats,
    NeighborhoodMarket,
    NeighborhoodStats,
    ObservationPeriod,
    PriceGroup,
)
from backend.infrastructure import config
from backend.schemas.market import MarketStatsResponse
from backend.services.market import MarketService

PERIOD = ObservationPeriod(start=date(2026, 10, 1), end=date(2026, 10, 9))


def _stats(
    n_observations: int,
    *,
    mean: int = 100_000,
    median: int | None = None,
) -> MarketStats:
    return MarketStats(
        n_observations=n_observations,
        mean_rent_price=mean,
        median_rent_price=median,
        p10_rent_price=50_000,
        p90_rent_price=200_000,
        min_rent_price=10_000,
        max_rent_price=400_000,
    )


def _quality() -> MarketQuality:
    return MarketQuality(
        n_price_bound=12,
        pct_price_bound=12.0,
        n_republication=25,
        pct_republication=25.0,
        n_neighborhood_unrecognized=3,
        pct_neighborhood_unrecognized=3.0,
    )


class FakeMarketRepository:
    """Dépôt en mémoire : enregistre les filtres reçus et rend des objets connus."""

    def __init__(
        self,
        *,
        period: ObservationPeriod = PERIOD,
        cities: list[CityMarket] | None = None,
        neighborhoods: list[NeighborhoodMarket] | None = None,
        prices: list[PriceGroup] | None = None,
    ) -> None:
        self.period = period
        self.city_rows = cities if cities is not None else [
            CityMarket("Douala", _stats(100, median=100_000), _quality()),
            CityMarket("Yaoundé", _stats(10, median=150_000), _quality()),
        ]
        self.neighborhood_rows = neighborhoods if neighborhoods is not None else [
            NeighborhoodMarket(
                city="Douala",
                neighborhood="Makepe",
                neighborhood_recognized=True,
                n_groups=2,
                stats=NeighborhoodStats(
                    n_observations=80,
                    mean_rent_price=120_000,
                    min_rent_price=20_000,
                    max_rent_price=300_000,
                ),
                quality=_quality(),
            )
        ]
        self.price_rows = prices if prices is not None else [
            PriceGroup(
                city="Douala",
                neighborhood="Makepe",
                neighborhood_recognized=True,
                property_type="apartment",
                bedrooms=2,
                stats=_stats(80, median=120_000),
                quality=_quality(),
            ),
            PriceGroup(
                city="Douala",
                neighborhood="Makepe",
                neighborhood_recognized=True,
                property_type="apartment",
                bedrooms=1,
                stats=_stats(5, median=40_000),
                quality=_quality(),
            ),
        ]
        self.calls: list[tuple[str, dict[str, object]]] = []

    def observation_period(self) -> ObservationPeriod:
        return self.period

    def cities(self) -> list[CityMarket]:
        return self.city_rows

    def neighborhoods(
        self,
        *,
        city: str,
        property_type: str | None = None,
        bedrooms: int | None = None,
    ) -> list[NeighborhoodMarket]:
        self.calls.append(
            ("neighborhoods", {"city": city, "property_type": property_type, "bedrooms": bedrooms})
        )
        return self.neighborhood_rows

    def prices(
        self,
        *,
        city: str | None = None,
        neighborhood: str | None = None,
        property_type: str | None = None,
        bedrooms: int | None = None,
    ) -> list[PriceGroup]:
        self.calls.append(
            (
                "prices",
                {
                    "city": city,
                    "neighborhood": neighborhood,
                    "property_type": property_type,
                    "bedrooms": bedrooms,
                },
            )
        )
        return self.price_rows


@pytest.fixture
def repository() -> FakeMarketRepository:
    return FakeMarketRepository()


@pytest.fixture
def client(repository: FakeMarketRepository) -> TestClient:
    app: FastAPI = create_app()
    app.dependency_overrides[get_market_service] = lambda: MarketService(repository)
    return TestClient(app)


def test_cities_expose_volume_period_and_quality(client: TestClient) -> None:
    response = client.get(f"{config.API_PREFIX}/market/cities")

    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "XAF"
    assert body["min_publish_n"] == 30
    assert body["observed_period"] == {"start": "2026-10-01", "end": "2026-10-09"}
    douala, yaounde = body["cities"]
    assert douala["city"] == "Douala"
    assert douala["stats"]["n_observations"] == 100
    assert douala["stats"]["median_published"] is True
    assert douala["quality"]["n_republication"] == 25
    assert douala["quality"]["n_neighborhood_unrecognized"] == 3


def test_cities_hide_median_under_publication_threshold(client: TestClient) -> None:
    """Défense en profondeur : une médiane sous 30 n'est jamais publiée."""
    response = client.get(f"{config.API_PREFIX}/market/cities")

    yaounde = response.json()["cities"][1]
    assert yaounde["stats"]["n_observations"] == 10
    assert yaounde["stats"]["median_rent_price"] is None
    assert yaounde["stats"]["median_published"] is False


def test_market_routes_are_in_openapi(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert f"{config.API_PREFIX}/market/cities" in paths
    assert f"{config.API_PREFIX}/market/neighborhoods" in paths
    assert f"{config.API_PREFIX}/market/prices" in paths


def test_neighborhoods_require_a_city(client: TestClient) -> None:
    response = client.get(f"{config.API_PREFIX}/market/neighborhoods")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_neighborhoods_reject_a_city_outside_the_vocabulary(client: TestClient) -> None:
    response = client.get(
        f"{config.API_PREFIX}/market/neighborhoods", params={"city": "Conakry"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_neighborhoods_forward_filters_and_expose_volume(
    client: TestClient, repository: FakeMarketRepository
) -> None:
    response = client.get(
        f"{config.API_PREFIX}/market/neighborhoods",
        params={"city": "Douala", "property_type": "apartment", "bedrooms": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Douala"
    assert body["n_observations"] == 80
    assert body["n_neighborhoods"] == 1
    assert body["neighborhoods"][0]["stats"]["n_observations"] == 80
    assert body["neighborhoods"][0]["neighborhood_recognized"] is True
    assert repository.calls == [
        (
            "neighborhoods",
            {"city": "Douala", "property_type": "apartment", "bedrooms": 2},
        )
    ]


def test_neighborhoods_do_not_expose_an_aggregated_median(client: TestClient) -> None:
    """Agréger des médianes serait faux : la synthèse quartier n'en publie pas."""
    response = client.get(
        f"{config.API_PREFIX}/market/neighborhoods", params={"city": "Douala"}
    )

    stats = response.json()["neighborhoods"][0]["stats"]
    assert "median_rent_price" not in stats
    assert "p10_rent_price" not in stats


def test_prices_publish_median_only_above_threshold(
    client: TestClient, repository: FakeMarketRepository
) -> None:
    response = client.get(
        f"{config.API_PREFIX}/market/prices", params={"city": "Douala"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["n_observations"] == 85
    published, hidden = body["groups"]
    assert published["stats"]["n_observations"] == 80
    assert published["stats"]["median_rent_price"] == 120_000
    assert published["stats"]["median_published"] is True
    assert hidden["stats"]["n_observations"] == 5
    assert hidden["stats"]["median_rent_price"] is None
    assert hidden["stats"]["median_published"] is False
    assert repository.calls == [
        (
            "prices",
            {"city": "Douala", "neighborhood": None, "property_type": None, "bedrooms": None},
        )
    ]


def test_prices_require_city_when_filtering_by_neighborhood(client: TestClient) -> None:
    response = client.get(
        f"{config.API_PREFIX}/market/prices", params={"neighborhood": "Makepe"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"
    assert "city" in response.json()["error"]["message"]


def test_prices_reject_invalid_room_bounds(client: TestClient) -> None:
    response = client.get(
        f"{config.API_PREFIX}/market/prices", params={"bedrooms": 11}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_prices_reject_a_malformed_period(client: TestClient) -> None:
    response = client.get(
        f"{config.API_PREFIX}/market/prices", params={"period": "2026-13"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_prices_return_an_explicit_empty_result_outside_observed_period(
    client: TestClient,
) -> None:
    response = client.get(
        f"{config.API_PREFIX}/market/prices", params={"period": "2026-09"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["n_observations"] == 0
    assert body["groups"] == []
    assert body["observed_period"] == {"start": "2026-10-01", "end": "2026-10-09"}


def test_prices_accept_the_observed_month(client: TestClient) -> None:
    response = client.get(
        f"{config.API_PREFIX}/market/prices", params={"period": "2026-10"}
    )

    assert response.status_code == 200
    assert response.json()["n_observations"] == 85


def test_prices_refuse_period_filter_when_data_spans_months() -> None:
    repository = FakeMarketRepository(
        period=ObservationPeriod(start=date(2026, 9, 1), end=date(2026, 10, 9))
    )
    app: FastAPI = create_app()
    app.dependency_overrides[get_market_service] = lambda: MarketService(repository)

    response = TestClient(app).get(
        f"{config.API_PREFIX}/market/prices", params={"period": "2026-10"}
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "bad_request"
    assert "plusieurs mois" in body["error"]["message"]


def test_prices_never_invent_a_statistic_on_empty_result() -> None:
    repository = FakeMarketRepository(prices=[])
    app: FastAPI = create_app()
    app.dependency_overrides[get_market_service] = lambda: MarketService(repository)

    response = TestClient(app).get(f"{config.API_PREFIX}/market/prices")

    assert response.status_code == 200
    assert response.json()["n_observations"] == 0
    assert response.json()["groups"] == []


def test_stats_schema_requires_observation_count() -> None:
    """L'invariant est porté par le schéma : impossible de l'omettre par oubli."""
    with pytest.raises(ValidationError):
        MarketStatsResponse(
            mean_rent_price=100_000,
            median_published=False,
            min_rent_price=1,
            max_rent_price=200_000,
        )
