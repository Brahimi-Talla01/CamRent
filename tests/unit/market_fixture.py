"""Dépôt de marché simulé, partagé par les tests des tickets #53 et #54.

Les valeurs sont volontairement petites et calculables à la main. Le dépôt
filtre réellement les lignes, comme le ferait PostgreSQL : c'est ce qui permet
de vérifier qu'un appel de comparaison utilise **le même groupe** que l'endpoint
de marché, sans dépendre d'une base.
"""

from __future__ import annotations

from datetime import date

from backend.domain.market import (
    CityMarket,
    MarketQuality,
    MarketStats,
    NeighborhoodMarket,
    NeighborhoodStats,
    ObservationPeriod,
    PriceGroup,
)

PERIOD = ObservationPeriod(start=date(2026, 10, 1), end=date(2026, 10, 9))


def market_stats(
    n_observations: int,
    *,
    mean: int = 100_000,
    median: int | None = None,
) -> MarketStats:
    """Statistiques de test, avec une fourchette fixe et lisible."""
    return MarketStats(
        n_observations=n_observations,
        mean_rent_price=mean,
        median_rent_price=median,
        p10_rent_price=50_000,
        p90_rent_price=200_000,
        min_rent_price=10_000,
        max_rent_price=400_000,
    )


def market_quality() -> MarketQuality:
    """Qualité de test : des biais non nuls, pour vérifier qu'ils sont transmis."""
    return MarketQuality(
        n_price_bound=12,
        pct_price_bound=12.0,
        n_republication=25,
        pct_republication=25.0,
        n_neighborhood_unrecognized=3,
        pct_neighborhood_unrecognized=3.0,
    )


class FakeMarketRepository:
    """Dépôt en mémoire : enregistre les filtres reçus et filtre réellement."""

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
            CityMarket("Douala", market_stats(100, median=100_000), market_quality()),
            CityMarket("Yaoundé", market_stats(10, median=150_000), market_quality()),
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
                quality=market_quality(),
            )
        ]
        self.price_rows = prices if prices is not None else [
            PriceGroup(
                city="Douala",
                neighborhood="Makepe",
                neighborhood_recognized=True,
                property_type="apartment",
                bedrooms=2,
                stats=market_stats(80, median=120_000),
                quality=market_quality(),
            ),
            PriceGroup(
                city="Douala",
                neighborhood="Makepe",
                neighborhood_recognized=True,
                property_type="apartment",
                bedrooms=1,
                stats=market_stats(5, median=40_000),
                quality=market_quality(),
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
            (
                "neighborhoods",
                {"city": city, "property_type": property_type, "bedrooms": bedrooms},
            )
        )
        # La synthèse quartier est déjà agrégée : le filtre de type/chambres ne
        # change pas la ligne simulée, seul le filtre de ville est appliqué.
        return [row for row in self.neighborhood_rows if row.city == city]

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
        return [
            row
            for row in self.price_rows
            if (city is None or row.city == city)
            and (neighborhood is None or row.neighborhood == neighborhood)
            and (property_type is None or row.property_type == property_type)
            and (bedrooms is None or row.bedrooms == bedrooms)
        ]
