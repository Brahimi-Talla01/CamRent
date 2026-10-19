"""Comparaison réelle : comparaison ↔ prédiction ↔ marts PostgreSQL (ticket #54).

Le modèle est le **fixture isolé** (comme dans les tests unitaires) : la CI n'a
pas de registre MLflow réel, mais elle a des marts construits par dbt. Le test
vérifie donc le chemin complet HTTP + service + SQL, et surtout que la
comparaison renvoie **exactement** les valeurs de `/predictions` et
`/market/prices` pour les mêmes paramètres.

Aucune valeur n'est figée : il s'exécute sur les données réelles comme sur le
jeu synthétique de la CI. Il est lancé après `dbt build`, avec
`DBT_MARTS_SCHEMA=analytics_ci_marts` dans la CI.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.api.app import create_app
from backend.api.routes import market as market_route
from backend.api.routes import predictions as predictions_route
from backend.infrastructure import config
from backend.ml.loader import PinnedModelProvider
from backend.ml.service import EstimationService, known_city_neighborhood_pairs
from backend.repositories.market import PostgresMarketRepository
from backend.services.market import MarketService
from tests.unit.serving_fixture import MODEL_VERSION, build_bundle, write_pin

pytestmark = pytest.mark.skipif(
    not os.environ.get(config.DATABASE_URL_ENV),
    reason=f"{config.DATABASE_URL_ENV} absente : comparaison aux marts non exécutée.",
)

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@pytest.fixture(scope="module")
def engine():
    database = create_engine(config.database_url(), future=True)
    try:
        yield database
    finally:
        database.dispose()


@pytest.fixture(scope="module")
def schema() -> str:
    value = config.market_marts_schema()
    assert _IDENTIFIER.match(value), f"schéma de marts invalide : {value!r}"
    return f'"{value}"'


@pytest.fixture(scope="module")
def bundle():
    return build_bundle()


@pytest.fixture(scope="module")
def repository(schema: str) -> PostgresMarketRepository:
    # `schema` est déjà validé ; le dépôt le revérifie de toute façon.
    repository = PostgresMarketRepository(
        config.database_url(), schema=schema.strip('"')
    )
    try:
        yield repository
    finally:
        repository.close()


@pytest.fixture(scope="module")
def client(
    bundle, repository: PostgresMarketRepository, tmp_path_factory
) -> TestClient:
    directory: Path = tmp_path_factory.mktemp("comparison-serving")
    provider = PinnedModelProvider(
        pin_path=write_pin(directory),
        model_loader=lambda pin: bundle.model,
        interval_loader=lambda pin: bundle.interval,
    )
    estimation = EstimationService(provider)
    market = MarketService(repository)
    app = create_app()
    app.dependency_overrides[predictions_route.get_estimation_service] = lambda: estimation
    app.dependency_overrides[market_route.get_market_service] = lambda: market
    return TestClient(app, raise_server_exceptions=False)


def _rows(engine, statement: str) -> list[dict[str, object]]:
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(text(statement)).mappings()
        ]


def _candidates(engine, schema: str, bundle) -> list[dict[str, object]]:
    """Groupes de marché dont le couple (ville, quartier) est connu du modèle."""
    known = known_city_neighborhood_pairs(bundle)
    rows = _rows(
        engine,
        f"""
        select city, neighborhood, property_type, bedrooms, n_observations,
               mean_rent_price, median_rent_price
        from {schema}.mart_neighborhood_prices
        where property_type = 'apartment' and bedrooms between 1 and 3
        order by n_observations desc, city, neighborhood, bedrooms
        """,
    )
    return [row for row in rows if (row["city"], row["neighborhood"]) in known]


def _listing(group: dict[str, object], asking_rent: int | None = None) -> dict[str, object]:
    return {
        "city": group["city"],
        "neighborhood": group["neighborhood"],
        "property_type": group["property_type"],
        "bedrooms": group["bedrooms"],
        "bathrooms": min(int(group["bedrooms"]), 2),
        "asking_rent": asking_rent
        if asking_rent is not None
        else int(group["mean_rent_price"]),
    }


def _compare(client: TestClient, *listings: dict[str, object]) -> dict[str, object]:
    response = client.post(
        f"{config.API_PREFIX}/comparisons", json={"listings": list(listings)}
    )
    assert response.status_code == 200, response.text
    return response.json()


def _prediction(client: TestClient, listing: dict[str, object]) -> dict[str, object]:
    payload = {key: value for key, value in listing.items() if key != "asking_rent"}
    response = client.post(f"{config.API_PREFIX}/predictions", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _market_group(client: TestClient, listing: dict[str, object]) -> dict[str, object] | None:
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
    assert len(groups) <= 1
    return groups[0] if groups else None


def test_comparison_matches_direct_endpoints(
    engine, schema: str, bundle, client: TestClient
) -> None:
    groups = _candidates(engine, schema, bundle)
    assert groups, "aucun groupe du mart ne correspond au domaine du modèle"
    listing = _listing(groups[0], asking_rent=int(groups[0]["mean_rent_price"]) + 15_000)

    body = _compare(client, listing)
    prediction = _prediction(client, listing)
    group = _market_group(client, listing)
    assert group is not None

    assert body["model_version"] == prediction["model_version"] == MODEL_VERSION
    item = body["comparisons"][0]
    assert item["listing"] == listing
    assert item["estimate"] == {
        "estimated_rent": prediction["estimated_rent"],
        "lower_bound": prediction["lower_bound"],
        "upper_bound": prediction["upper_bound"],
    }
    assert item["market"]["n_observations"] == group["stats"]["n_observations"]
    assert item["market"]["mean_rent_price"] == group["stats"]["mean_rent_price"]
    assert item["market"]["median_rent_price"] == group["stats"]["median_rent_price"]
    assert item["market"]["median_published"] == group["stats"]["median_published"]
    assert item["market"]["quality"] == group["quality"]
    assert item["gaps"]["to_estimate"]["absolute"] == (
        listing["asking_rent"] - prediction["estimated_rent"]
    )
    assert item["gaps"]["to_market_mean"]["absolute"] == (
        listing["asking_rent"] - group["stats"]["mean_rent_price"]
    )


def test_median_threshold_is_respected_on_real_mart(
    engine, schema: str, bundle, client: TestClient
) -> None:
    groups = [row for row in _candidates(engine, schema, bundle) if row["n_observations"] < 30]
    assert groups, "le mart doit contenir un groupe sous le seuil pour ce test"
    listing = _listing(groups[0])

    body = _compare(client, listing)
    market = body["comparisons"][0]["market"]

    assert market["n_observations"] == groups[0]["n_observations"]
    assert market["median_rent_price"] is None
    assert market["median_published"] is False
    assert body["comparisons"][0]["gaps"]["to_market_median"] is None
    assert body["comparisons"][0]["gaps"]["to_market_mean"] is not None


def test_multiple_listings_are_compared_independently(
    engine, schema: str, bundle, client: TestClient
) -> None:
    groups = _candidates(engine, schema, bundle)
    assert len(groups) >= 2, "il faut au moins deux groupes pour la comparaison multiple"
    listings = [_listing(groups[0]), _listing(groups[1], asking_rent=50_000)]

    body = _compare(client, *listings)

    assert len(body["comparisons"]) == 2
    assert [item["listing"] for item in body["comparisons"]] == listings
    for item, listing in zip(body["comparisons"], listings, strict=True):
        prediction = _prediction(client, listing)
        group = _market_group(client, listing)
        assert item["estimate"]["estimated_rent"] == prediction["estimated_rent"]
        assert item["market"]["n_observations"] == group["stats"]["n_observations"]
        assert item["gaps"]["to_estimate"]["absolute"] == (
            listing["asking_rent"] - prediction["estimated_rent"]
        )


def test_absent_market_group_returns_null_without_inventing(
    engine, schema: str, bundle, client: TestClient
) -> None:
    known = known_city_neighborhood_pairs(bundle)
    existing = {
        (row["city"], row["neighborhood"], row["property_type"], row["bedrooms"])
        for row in _rows(
            engine,
            f"""
            select city, neighborhood, property_type, bedrooms
            from {schema}.mart_neighborhood_prices
            """,
        )
    }
    city, neighborhood = sorted(known)[0]
    absent = next(
        (
            (kind, bedrooms)
            for kind in ("apartment", "studio", "house", "room")
            for bedrooms in range(0, 11)
            if (city, neighborhood, kind, bedrooms) not in existing
        ),
        None,
    )
    assert absent is not None, "le mart couvre toutes les combinaisons : cas absent impossible"
    kind, bedrooms = absent
    listing = {
        "city": city,
        "neighborhood": neighborhood,
        "property_type": kind,
        "bedrooms": bedrooms,
        "bathrooms": 1,
        "asking_rent": 100_000,
    }

    assert _market_group(client, listing) is None
    body = _compare(client, listing)
    item = body["comparisons"][0]

    assert item["market"] is None
    assert item["gaps"]["to_market_mean"] is None
    assert item["gaps"]["to_market_median"] is None
    assert item["gaps"]["to_estimate"]["absolute"] == (
        100_000 - item["estimate"]["estimated_rent"]
    )
