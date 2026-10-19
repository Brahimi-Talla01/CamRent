"""Lecture des marts de marché en PostgreSQL (ticket #53).

Les statistiques viennent **exclusivement** des marts dbt
(`mart_city_prices`, `mart_neighborhood_prices`, `mart_property_prices`) : le
backend ne recalcule aucun agrégat de marché, il ne lit ni `landing` ni les
données brutes.

Deux synthèses sont faites en SQL, et seulement celles qui sont exactes à partir
des agrégats existants :

- le total d'observations d'un quartier (`sum(n_observations)`) ;
- sa moyenne (`sum(moyenne × N) / sum(N)`), la moyenne pondérée par les effectifs.

Aucune médiane ni aucun centile n'est agrégé : ce serait mathématiquement faux.
Le détail par (type, chambres), avec le seuil de publication, est exposé par
`/market/prices`.

Le schéma est configurable (`DBT_MARTS_SCHEMA`) parce que la CI construit ses
marts dans un schéma dédié. Il est validé avant interpolation : seuls les
identifiants PostgreSQL simples sont acceptés, le reste étant refusé.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Protocol

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ..domain.market import (
    CityMarket,
    MarketQuality,
    MarketStats,
    NeighborhoodMarket,
    NeighborhoodStats,
    ObservationPeriod,
    PriceGroup,
)
from ..infrastructure import config

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class MarketRepository(Protocol):
    """Accès en lecture aux statistiques de marché (implémentable en test)."""

    def cities(self) -> list[CityMarket]:
        """Statistiques par ville, de la plus représentée à la moins représentée."""

    def neighborhoods(
        self,
        *,
        city: str,
        property_type: str | None = None,
        bedrooms: int | None = None,
    ) -> list[NeighborhoodMarket]:
        """Synthèse par quartier d'une ville, avec les filtres disponibles."""

    def prices(
        self,
        *,
        city: str | None = None,
        neighborhood: str | None = None,
        property_type: str | None = None,
        bedrooms: int | None = None,
    ) -> list[PriceGroup]:
        """Groupes de prix correspondant aux filtres."""

    def observation_period(self) -> ObservationPeriod:
        """Première et dernière date réellement observées."""


class PostgresMarketRepository:
    """Implémentation PostgreSQL : lectures seules, paramètres liés."""

    def __init__(self, database_url: str, *, schema: str | None = None) -> None:
        self._schema = schema or config.market_marts_schema()
        if not _IDENTIFIER.match(self._schema):
            raise ValueError(
                f"{config.MARTS_SCHEMA_ENV} doit être un identifiant PostgreSQL simple "
                f"(reçu : {self._schema!r})."
            )
        self._engine: Engine = create_engine(database_url, future=True)

    def _table(self, name: str) -> str:
        return f'"{self._schema}"."{name}"'

    def _fetch(self, statement: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._engine.connect() as connection:
            result = connection.execute(text(statement), params or {})
            return [dict(row) for row in result.mappings()]

    def close(self) -> None:
        """Libère le pool de connexions (tests et arrêt propre)."""
        self._engine.dispose()

    # --- Villes ---------------------------------------------------------

    def cities(self) -> list[CityMarket]:
        rows = self._fetch(
            f"""
            select city,
                   n_observations,
                   mean_rent_price,
                   median_rent_price,
                   p10_rent_price,
                   p90_rent_price,
                   min_rent_price,
                   max_rent_price,
                   n_price_bound,
                   pct_price_bound,
                   n_republication,
                   pct_republication,
                   n_neighborhood_unrecognized,
                   pct_neighborhood_unrecognized
            from {self._table("mart_city_prices")}
            order by n_observations desc, city
            """
        )
        return [
            CityMarket(
                city=str(row["city"]),
                stats=_stats(row),
                quality=_quality(row, with_neighborhoods=True),
            )
            for row in rows
        ]

    # --- Quartiers ------------------------------------------------------

    def neighborhoods(
        self,
        *,
        city: str,
        property_type: str | None = None,
        bedrooms: int | None = None,
    ) -> list[NeighborhoodMarket]:
        filters = ["city = :city"]
        params: dict[str, Any] = {"city": city}
        if property_type is not None:
            filters.append("property_type = :property_type")
            params["property_type"] = property_type
        if bedrooms is not None:
            filters.append("bedrooms = :bedrooms")
            params["bedrooms"] = bedrooms
        where = " and ".join(filters)

        rows = self._fetch(
            f"""
            select city,
                   neighborhood,
                   bool_and(neighborhood_recognized) as neighborhood_recognized,
                   count(*)::integer as n_groups,
                   sum(n_observations)::bigint as n_observations,
                   round(
                       sum(mean_rent_price::numeric * n_observations)
                       / sum(n_observations)
                   )::bigint as mean_rent_price,
                   min(min_rent_price)::bigint as min_rent_price,
                   max(max_rent_price)::bigint as max_rent_price,
                   sum(n_price_bound)::bigint as n_price_bound,
                   round(
                       100.0 * sum(n_price_bound) / sum(n_observations)
                   )::double precision as pct_price_bound,
                   sum(n_republication)::bigint as n_republication,
                   round(
                       100.0 * sum(n_republication) / sum(n_observations)
                   )::double precision as pct_republication
            from {self._table("mart_neighborhood_prices")}
            where {where}
            group by city, neighborhood
            order by n_observations desc, neighborhood
            """,
            params,
        )
        return [
            NeighborhoodMarket(
                city=str(row["city"]),
                neighborhood=str(row["neighborhood"]),
                neighborhood_recognized=bool(row["neighborhood_recognized"]),
                n_groups=int(row["n_groups"]),
                stats=NeighborhoodStats(
                    n_observations=int(row["n_observations"]),
                    mean_rent_price=int(row["mean_rent_price"]),
                    min_rent_price=int(row["min_rent_price"]),
                    max_rent_price=int(row["max_rent_price"]),
                ),
                quality=_quality(row, with_neighborhoods=False),
            )
            for row in rows
        ]

    # --- Prix -----------------------------------------------------------

    def prices(
        self,
        *,
        city: str | None = None,
        neighborhood: str | None = None,
        property_type: str | None = None,
        bedrooms: int | None = None,
    ) -> list[PriceGroup]:
        """Choisit le mart dont le grain couvre exactement les filtres.

        - un quartier ou un nombre de chambres demandé → grain fin
          (ville, quartier, type, chambres) ;
        - seulement un type de bien → grain (type, ville) ;
        - aucun filtre de détail → grain ville.

        On ne mélange jamais deux grains dans une même statistique : chaque
        groupe retourné porte ses propres dimensions et son propre N.
        """
        if neighborhood is not None or bedrooms is not None:
            return self._prices_by_group(
                city=city,
                neighborhood=neighborhood,
                property_type=property_type,
                bedrooms=bedrooms,
            )
        if property_type is not None:
            return self._prices_by_property(city=city, property_type=property_type)
        return self._prices_by_city(city=city)

    def _prices_by_group(
        self,
        *,
        city: str | None,
        neighborhood: str | None,
        property_type: str | None,
        bedrooms: int | None,
    ) -> list[PriceGroup]:
        filters: list[str] = []
        params: dict[str, Any] = {}
        for column, value in (
            ("city", city),
            ("neighborhood", neighborhood),
            ("property_type", property_type),
            ("bedrooms", bedrooms),
        ):
            if value is not None:
                filters.append(f"{column} = :{column}")
                params[column] = value
        where = f"where {' and '.join(filters)}" if filters else ""

        rows = self._fetch(
            f"""
            select city,
                   neighborhood,
                   neighborhood_recognized,
                   property_type,
                   bedrooms,
                   n_observations,
                   mean_rent_price,
                   median_rent_price,
                   p10_rent_price,
                   p90_rent_price,
                   min_rent_price,
                   max_rent_price,
                   n_price_bound,
                   pct_price_bound,
                   n_republication,
                   pct_republication
            from {self._table("mart_neighborhood_prices")}
            {where}
            order by n_observations desc, city, neighborhood, property_type, bedrooms
            """,
            params,
        )
        return [
            PriceGroup(
                city=str(row["city"]),
                neighborhood=str(row["neighborhood"]),
                neighborhood_recognized=bool(row["neighborhood_recognized"]),
                property_type=str(row["property_type"]),
                bedrooms=int(row["bedrooms"]),
                stats=_stats(row),
                quality=_quality(row, with_neighborhoods=False),
            )
            for row in rows
        ]

    def _prices_by_property(
        self, *, city: str | None, property_type: str
    ) -> list[PriceGroup]:
        filters = ["property_type = :property_type"]
        params: dict[str, Any] = {"property_type": property_type}
        if city is not None:
            filters.append("city = :city")
            params["city"] = city

        rows = self._fetch(
            f"""
            select city,
                   null::text as neighborhood,
                   null::boolean as neighborhood_recognized,
                   property_type,
                   null::smallint as bedrooms,
                   n_observations,
                   mean_rent_price,
                   median_rent_price,
                   p10_rent_price,
                   p90_rent_price,
                   min_rent_price,
                   max_rent_price,
                   n_price_bound,
                   pct_price_bound,
                   n_republication,
                   pct_republication
            from {self._table("mart_property_prices")}
            where {' and '.join(filters)}
            order by n_observations desc, city, property_type
            """,
            params,
        )
        return [
            PriceGroup(
                city=str(row["city"]),
                neighborhood=None,
                neighborhood_recognized=None,
                property_type=str(row["property_type"]),
                bedrooms=None,
                stats=_stats(row),
                quality=_quality(row, with_neighborhoods=False),
            )
            for row in rows
        ]

    def _prices_by_city(self, *, city: str | None) -> list[PriceGroup]:
        where = "where city = :city" if city is not None else ""
        params: dict[str, Any] = {"city": city} if city is not None else {}
        rows = self._fetch(
            f"""
            select city,
                   null::text as neighborhood,
                   null::boolean as neighborhood_recognized,
                   null::text as property_type,
                   null::smallint as bedrooms,
                   n_observations,
                   mean_rent_price,
                   median_rent_price,
                   p10_rent_price,
                   p90_rent_price,
                   min_rent_price,
                   max_rent_price,
                   n_price_bound,
                   pct_price_bound,
                   n_republication,
                   pct_republication,
                   n_neighborhood_unrecognized,
                   pct_neighborhood_unrecognized
            from {self._table("mart_city_prices")}
            {where}
            order by n_observations desc, city
            """,
            params,
        )
        return [
            PriceGroup(
                city=str(row["city"]),
                neighborhood=None,
                neighborhood_recognized=None,
                property_type=None,
                bedrooms=None,
                stats=_stats(row),
                quality=_quality(row, with_neighborhoods=True),
            )
            for row in rows
        ]

    # --- Période observée ----------------------------------------------

    def observation_period(self) -> ObservationPeriod:
        rows = self._fetch(
            f"""
            select min(date_day) as period_start,
                   max(date_day) as period_end
            from {self._table("fct_rent_observations")}
            """
        )
        row = rows[0] if rows else {"period_start": None, "period_end": None}
        start = row["period_start"]
        end = row["period_end"]
        return ObservationPeriod(
            start=date.fromisoformat(start) if start else None,
            end=date.fromisoformat(end) if end else None,
        )


def _stats(row: dict[str, Any]) -> MarketStats:
    """Mappe une ligne de mart vers des statistiques typées."""
    return MarketStats(
        n_observations=int(row["n_observations"]),
        mean_rent_price=int(row["mean_rent_price"]),
        median_rent_price=_int_or_none(row.get("median_rent_price")),
        p10_rent_price=_int_or_none(row.get("p10_rent_price")),
        p90_rent_price=_int_or_none(row.get("p90_rent_price")),
        min_rent_price=int(row["min_rent_price"]),
        max_rent_price=int(row["max_rent_price"]),
    )


def _quality(row: dict[str, Any], *, with_neighborhoods: bool) -> MarketQuality:
    """Mappe les drapeaux de qualité ; les absents restent `None`, jamais 0."""
    return MarketQuality(
        n_price_bound=int(row["n_price_bound"]),
        pct_price_bound=float(row["pct_price_bound"]),
        n_republication=int(row["n_republication"]),
        pct_republication=float(row["pct_republication"]),
        n_neighborhood_unrecognized=(
            _int_or_none(row.get("n_neighborhood_unrecognized")) if with_neighborhoods else None
        ),
        pct_neighborhood_unrecognized=(
            _float_or_none(row.get("pct_neighborhood_unrecognized"))
            if with_neighborhoods
            else None
        ),
    )


def _int_or_none(value: Any) -> int | None:
    return None if value is None else int(value)


def _float_or_none(value: Any) -> float | None:
    return None if value is None else float(value)
