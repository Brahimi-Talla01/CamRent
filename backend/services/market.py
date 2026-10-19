"""Service de marché : assemble les réponses de l'API publique (ticket #53).

La logique ici est volontairement mince : le dépôt lit les marts, le service met
en forme et applique les règles de l'API.

Trois règles, toutes vérifiables par test :

1. **Toute statistique porte son N.** Les schémas l'exigent ; le service ne
   construit jamais un objet sans effectif.
2. **Aucune médiane sous le seuil.** Le seuil `min_publish_n` est réappliqué ici,
   même si le mart en exposait une : défense en profondeur, jamais une médiane
   publiée par accident.
3. **Le filtre `period` ne ment pas.** Les marts n'ont pas de dimension
   temporelle ; tant que les observations tiennent dans un seul mois, le filtre
   est accepté pour ce mois et renvoie un résultat vide explicite pour tout autre
   mois. Si les données couvrent plusieurs mois, le filtre est refusé (400)
   plutôt que de renvoyer des statistiques toutes périodes sous une étiquette
   mensuelle.
"""

from __future__ import annotations

from datetime import date

from ..domain import market as domain
from ..repositories.market import MarketRepository
from ..schemas.market import (
    CitiesResponse,
    CityMarketResponse,
    MarketQualityResponse,
    MarketStatsResponse,
    NeighborhoodMarketResponse,
    NeighborhoodsResponse,
    NeighborhoodStatsResponse,
    ObservedPeriodResponse,
    PriceGroupResponse,
    PricesResponse,
)


class InvalidMarketFilterError(ValueError):
    """Combinaison de filtres qui ne peut pas produire une statistique honnête."""


class PeriodFilterUnavailableError(ValueError):
    """Filtre `period` demandé alors que les marts couvrent plusieurs mois."""


class MarketService:
    """Réponses de marché dérivées des marts, sans recalcul de statistiques."""

    def __init__(
        self,
        repository: MarketRepository,
        *,
        min_publish_n: int = domain.MIN_PUBLISH_N,
    ) -> None:
        self._repository = repository
        self._min_publish_n = min_publish_n

    # --- Villes ---------------------------------------------------------

    def cities(self) -> CitiesResponse:
        period = self._repository.observation_period()
        cities = self._repository.cities()
        return CitiesResponse(
            currency=domain.CURRENCY,
            min_publish_n=self._min_publish_n,
            observed_period=_period_response(period),
            cities=[
                CityMarketResponse(
                    city=city.city,
                    stats=self._stats_response(city.stats),
                    quality=_quality_response(city.quality),
                )
                for city in cities
            ],
        )

    # --- Quartiers ------------------------------------------------------

    def neighborhoods(
        self,
        *,
        city: str,
        property_type: str | None = None,
        bedrooms: int | None = None,
    ) -> NeighborhoodsResponse:
        period = self._repository.observation_period()
        neighborhoods = self._repository.neighborhoods(
            city=city, property_type=property_type, bedrooms=bedrooms
        )
        return NeighborhoodsResponse(
            currency=domain.CURRENCY,
            min_publish_n=self._min_publish_n,
            observed_period=_period_response(period),
            city=city,
            n_observations=sum(item.stats.n_observations for item in neighborhoods),
            n_neighborhoods=len(neighborhoods),
            neighborhoods=[
                NeighborhoodMarketResponse(
                    neighborhood=item.neighborhood,
                    neighborhood_recognized=item.neighborhood_recognized,
                    n_groups=item.n_groups,
                    stats=NeighborhoodStatsResponse(
                        n_observations=item.stats.n_observations,
                        mean_rent_price=item.stats.mean_rent_price,
                        min_rent_price=item.stats.min_rent_price,
                        max_rent_price=item.stats.max_rent_price,
                    ),
                    quality=_quality_response(item.quality),
                )
                for item in neighborhoods
            ],
        )

    # --- Prix -----------------------------------------------------------

    def prices(
        self,
        *,
        city: str | None = None,
        neighborhood: str | None = None,
        property_type: str | None = None,
        bedrooms: int | None = None,
        period: str | None = None,
    ) -> PricesResponse:
        if neighborhood is not None and city is None:
            raise InvalidMarketFilterError(
                "Le filtre `neighborhood` exige le filtre `city` : un quartier "
                "n'est pas unique entre les villes."
            )

        observed = self._repository.observation_period()
        if period is not None and not self._period_matches(period, observed):
            # Période hors des données : réponse vide **explicite**, jamais une
            # statistique d'une autre période présentée comme celle demandée.
            return PricesResponse(
                currency=domain.CURRENCY,
                min_publish_n=self._min_publish_n,
                observed_period=_period_response(observed),
                n_observations=0,
                groups=[],
            )

        groups = self._repository.prices(
            city=city,
            neighborhood=neighborhood,
            property_type=property_type,
            bedrooms=bedrooms,
        )
        return PricesResponse(
            currency=domain.CURRENCY,
            min_publish_n=self._min_publish_n,
            observed_period=_period_response(observed),
            n_observations=sum(group.stats.n_observations for group in groups),
            groups=[
                PriceGroupResponse(
                    city=group.city,
                    neighborhood=group.neighborhood,
                    neighborhood_recognized=group.neighborhood_recognized,
                    property_type=group.property_type,
                    bedrooms=group.bedrooms,
                    stats=self._stats_response(group.stats),
                    quality=_quality_response(group.quality),
                )
                for group in groups
            ],
        )

    # --- Règles ---------------------------------------------------------

    def _period_matches(self, period: str, observed: domain.ObservationPeriod) -> bool:
        """Le mois demandé est-il exactement celui que couvrent les marts ?

        Raises:
            PeriodFilterUnavailableError: si les données couvrent plusieurs mois
                (le filtre n'est pas supporté par les marts actuels).
        """
        if observed.start is None or observed.end is None:
            return False
        if _month(observed.start) != _month(observed.end):
            raise PeriodFilterUnavailableError(
                "Le filtre `period` n'est pas disponible : les marts couvrent "
                "plusieurs mois et n'exposent pas encore de dimension temporelle. "
                "Les statistiques retournées sont toutes périodes."
            )
        return period == _month(observed.start)

    def _stats_response(self, stats: domain.MarketStats) -> MarketStatsResponse:
        """Applique le seuil de publication, en plus du filtre dbt."""
        if stats.n_observations < self._min_publish_n:
            median: int | None = None
        else:
            median = stats.median_rent_price
        return MarketStatsResponse(
            n_observations=stats.n_observations,
            mean_rent_price=stats.mean_rent_price,
            median_rent_price=median,
            median_published=median is not None,
            p10_rent_price=stats.p10_rent_price,
            p90_rent_price=stats.p90_rent_price,
            min_rent_price=stats.min_rent_price,
            max_rent_price=stats.max_rent_price,
        )


def _month(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _period_response(period: domain.ObservationPeriod) -> ObservedPeriodResponse:
    return ObservedPeriodResponse(start=period.start, end=period.end)


def _quality_response(quality: domain.MarketQuality) -> MarketQualityResponse:
    return MarketQualityResponse(
        n_price_bound=quality.n_price_bound,
        pct_price_bound=quality.pct_price_bound,
        n_republication=quality.n_republication,
        pct_republication=quality.pct_republication,
        n_neighborhood_unrecognized=quality.n_neighborhood_unrecognized,
        pct_neighborhood_unrecognized=quality.pct_neighborhood_unrecognized,
    )
