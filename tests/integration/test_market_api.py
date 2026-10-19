"""Comparaison réelle entre l'API de marché et les marts PostgreSQL (ticket #53).

Ce test ne fixe aucun chiffre : il lit les marts et vérifie que l'API renvoie
**exactement** les mêmes valeurs, y compris le seuil de publication et la
période observée. Il s'exécute donc aussi bien sur les données réelles que sur
le jeu synthétique de la CI.

Il est séparé de `tests/unit/` parce qu'il exige une base construite par dbt.
La CI l'exécute après `dbt build`, avec `DBT_MARTS_SCHEMA=analytics_ci_marts`.
"""

from __future__ import annotations

import os
import re
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.api.app import create_app
from backend.infrastructure import config

pytestmark = pytest.mark.skipif(
    not os.environ.get(config.DATABASE_URL_ENV),
    reason=f"{config.DATABASE_URL_ENV} absente : comparaison aux marts non exécutée.",
)

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@pytest.fixture(scope="module")
def engine():
    url = config.database_url()
    database = create_engine(url, future=True)
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
def client() -> TestClient:
    return TestClient(create_app())


def _rows(engine, statement: str, **params: object) -> list[dict[str, object]]:
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(text(statement), params).mappings()
        ]


def _get(client: TestClient, path: str, **params: object) -> dict[str, object]:
    response = client.get(f"{config.API_PREFIX}{path}", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_cities_match_the_mart(engine, schema: str, client: TestClient) -> None:
    expected = _rows(
        engine,
        f"""
        select city, n_observations, mean_rent_price, median_rent_price,
               p10_rent_price, p90_rent_price, min_rent_price, max_rent_price,
               n_price_bound, pct_price_bound, n_republication, pct_republication,
               n_neighborhood_unrecognized, pct_neighborhood_unrecognized
        from {schema}.mart_city_prices
        order by n_observations desc, city
        """,
    )
    body = _get(client, "/market/cities")

    assert [city["city"] for city in body["cities"]] == [row["city"] for row in expected]
    for actual, row in zip(body["cities"], expected, strict=True):
        stats = actual["stats"]
        quality = actual["quality"]
        assert stats["n_observations"] == row["n_observations"]
        assert stats["mean_rent_price"] == row["mean_rent_price"]
        assert stats["median_rent_price"] == row["median_rent_price"]
        assert stats["p10_rent_price"] == row["p10_rent_price"]
        assert stats["p90_rent_price"] == row["p90_rent_price"]
        assert stats["min_rent_price"] == row["min_rent_price"]
        assert stats["max_rent_price"] == row["max_rent_price"]
        assert quality["n_price_bound"] == row["n_price_bound"]
        assert quality["pct_price_bound"] == row["pct_price_bound"]
        assert quality["n_republication"] == row["n_republication"]
        assert quality["pct_republication"] == row["pct_republication"]
        assert quality["n_neighborhood_unrecognized"] == row["n_neighborhood_unrecognized"]
        assert (
            quality["pct_neighborhood_unrecognized"]
            == row["pct_neighborhood_unrecognized"]
        )


def test_neighborhoods_match_the_mart(engine, schema: str, client: TestClient) -> None:
    city = _rows(engine, f"select city from {schema}.mart_city_prices order by city limit 1")[0][
        "city"
    ]
    expected = _rows(
        engine,
        f"""
        select neighborhood,
               bool_and(neighborhood_recognized) as neighborhood_recognized,
               count(*)::integer as n_groups,
               sum(n_observations)::bigint as n_observations,
               round(
                   sum(mean_rent_price::numeric * n_observations) / sum(n_observations)
               )::bigint as mean_rent_price,
               min(min_rent_price)::bigint as min_rent_price,
               max(max_rent_price)::bigint as max_rent_price,
               sum(n_price_bound)::bigint as n_price_bound,
               sum(n_republication)::bigint as n_republication
        from {schema}.mart_neighborhood_prices
        where city = :city
        group by neighborhood
        order by n_observations desc, neighborhood
        """,
        city=city,
    )
    body = _get(client, "/market/neighborhoods", city=city)

    assert body["city"] == city
    assert body["n_neighborhoods"] == len(expected)
    assert body["n_observations"] == sum(row["n_observations"] for row in expected)
    for actual, row in zip(body["neighborhoods"], expected, strict=True):
        assert actual["neighborhood"] == row["neighborhood"]
        assert actual["neighborhood_recognized"] == row["neighborhood_recognized"]
        assert actual["n_groups"] == row["n_groups"]
        assert actual["stats"]["n_observations"] == row["n_observations"]
        assert actual["stats"]["mean_rent_price"] == row["mean_rent_price"]
        assert actual["stats"]["min_rent_price"] == row["min_rent_price"]
        assert actual["stats"]["max_rent_price"] == row["max_rent_price"]
        assert actual["quality"]["n_price_bound"] == row["n_price_bound"]
        assert actual["quality"]["n_republication"] == row["n_republication"]


def test_price_groups_match_the_mart_and_its_threshold(
    engine, schema: str, client: TestClient
) -> None:
    rows = _rows(
        engine,
        f"""
        select city, neighborhood, property_type, bedrooms, n_observations,
               mean_rent_price, median_rent_price, p10_rent_price, p90_rent_price,
               min_rent_price, max_rent_price, n_price_bound, n_republication
        from {schema}.mart_neighborhood_prices
        where n_observations < 30
        order by n_observations desc
        limit 1
        """,
    )
    assert rows, "le mart doit contenir au moins un groupe sous le seuil au MVP"
    row = rows[0]
    body = _get(
        client,
        "/market/prices",
        city=row["city"],
        neighborhood=row["neighborhood"],
        property_type=row["property_type"],
        bedrooms=row["bedrooms"],
    )

    assert body["n_observations"] == row["n_observations"]
    assert len(body["groups"]) == 1
    group = body["groups"][0]
    assert group["stats"]["n_observations"] == row["n_observations"]
    assert group["stats"]["mean_rent_price"] == row["mean_rent_price"]
    assert group["stats"]["median_rent_price"] is None
    assert group["stats"]["median_published"] is False
    assert group["stats"]["p10_rent_price"] == row["p10_rent_price"]
    assert group["stats"]["p90_rent_price"] == row["p90_rent_price"]
    assert group["quality"]["n_price_bound"] == row["n_price_bound"]
    assert group["quality"]["n_republication"] == row["n_republication"]


def test_published_medians_match_the_mart(engine, schema: str, client: TestClient) -> None:
    rows = _rows(
        engine,
        f"""
        select city, neighborhood, property_type, bedrooms, n_observations,
               median_rent_price
        from {schema}.mart_neighborhood_prices
        where median_rent_price is not null
        order by n_observations desc
        limit 3
        """,
    )
    assert rows, "le mart doit publier au moins une médiane au MVP"
    for row in rows:
        body = _get(
            client,
            "/market/prices",
            city=row["city"],
            neighborhood=row["neighborhood"],
            property_type=row["property_type"],
            bedrooms=row["bedrooms"],
        )
        group = body["groups"][0]
        assert group["stats"]["n_observations"] == row["n_observations"]
        assert group["stats"]["median_rent_price"] == row["median_rent_price"]
        assert group["stats"]["median_published"] is True


def test_every_returned_median_respects_the_threshold(
    engine, schema: str, client: TestClient
) -> None:
    """Aucune réponse ne publie de médiane sous 30 observations, quel que soit le filtre."""
    city = _rows(engine, f"select city from {schema}.mart_city_prices order by city limit 1")[0][
        "city"
    ]
    body = _get(client, "/market/prices", city=city)

    assert body["groups"], "la ville interrogée doit avoir des groupes"
    for group in body["groups"]:
        stats = group["stats"]
        if stats["n_observations"] < body["min_publish_n"]:
            assert stats["median_rent_price"] is None
            assert stats["median_published"] is False
        else:
            assert stats["median_published"] is (stats["median_rent_price"] is not None)


def test_observed_period_and_period_filter_match_the_data(
    engine, schema: str, client: TestClient
) -> None:
    row = _rows(
        engine,
        f"""
        select min(date_day) as period_start, max(date_day) as period_end
        from {schema}.fct_rent_observations
        """,
    )[0]
    expected_start = date.fromisoformat(row["period_start"])
    expected_end = date.fromisoformat(row["period_end"])

    body = _get(client, "/market/prices")
    assert body["observed_period"] == {
        "start": expected_start.isoformat(),
        "end": expected_end.isoformat(),
    }

    if (expected_start.year, expected_start.month) == (expected_end.year, expected_end.month):
        month = f"{expected_start.year:04d}-{expected_start.month:02d}"
        matching = _get(client, "/market/prices", period=month)
        assert matching["n_observations"] == body["n_observations"]
        outside = _get(client, "/market/prices", period="1900-01")
        assert outside["n_observations"] == 0
        assert outside["groups"] == []


def test_empty_filter_is_explicit_and_not_invented(client: TestClient) -> None:
    body = _get(
        client,
        "/market/prices",
        city="Douala",
        neighborhood="Quartier qui n'existe pas",
    )

    assert body["n_observations"] == 0
    assert body["groups"] == []
    assert body["observed_period"]["start"]
