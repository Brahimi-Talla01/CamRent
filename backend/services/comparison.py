"""Service de comparaison : confronte un prix demandé à l'estimation et au marché.

Le service **ne calcule aucune statistique de marché** et **n'entraîne rien** :
il appelle exactement les deux briques déjà servies par l'API publique —

- `EstimationService.estimate` (endpoint 08a.2) pour l'estimation et sa fourchette ;
- `MarketService.prices` (endpoint 08a.4) pour le groupe local, son N, sa moyenne,
  sa médiane et son seuil de publication.

C'est ce qui garantit, par construction, que la comparaison ne diverge pas des
deux endpoints directs. Le seul calcul propre est l'écart signé
`asking_rent - référence` et sa valeur relative.

Le groupe de comparaison est le grain du mart : (ville, quartier, type, chambres).
Les salles de bain influencent l'estimation mais pas la référence locale, qui
n'existe pas à ce grain dans les données. Si le groupe est absent, la réponse
l'indique (`market: null`) au lieu d'élargir silencieusement la comparaison.
"""

from __future__ import annotations

from ..ml.service import EstimationService, ServingError
from ..schemas.comparison import (
    ComparisonEstimateResponse,
    ComparisonGapsResponse,
    ComparisonItemResponse,
    ComparisonMarketResponse,
    ComparisonRequest,
    ComparisonResponse,
    GapResponse,
)
from ..schemas.prediction import PredictionRequest
from .market import MarketService


class ComparisonService:
    """Compare des logements à l'estimation épinglée et au marché local."""

    def __init__(self, estimation: EstimationService, market: MarketService) -> None:
        self._estimation = estimation
        self._market = market

    def compare(self, request: ComparisonRequest) -> ComparisonResponse:
        """Construit une comparaison par logement, dans l'ordre de la requête.

        Raises:
            UnknownNeighborhoodError: propagée telle quelle par le service
                d'estimation — la route la traduit en 404, comme `/predictions`.
                Aucune comparaison partielle n'est retournée.
            ServingError: versions de modèle hétérogènes pendant la requête
                (invariant interne, ne doit pas arriver avec un pin stable).
        """
        items: list[ComparisonItemResponse] = []
        model_versions: set[str] = set()
        currency = "XAF"
        min_publish_n = 0

        for listing in request.listings:
            prediction_request = PredictionRequest.model_validate(
                listing.model_dump(mode="json", exclude={"asking_rent"})
            )
            prediction = self._estimation.estimate(prediction_request)
            model_versions.add(prediction.model_version)
            currency = prediction.currency

            market = self._market.prices(
                city=listing.city.value,
                neighborhood=listing.neighborhood,
                property_type=listing.property_type.value,
                bedrooms=listing.bedrooms,
            )
            min_publish_n = market.min_publish_n
            group = market.groups[0] if market.groups else None

            to_estimate = _gap(listing.asking_rent, prediction.estimated_rent)
            if to_estimate is None:  # estimation toujours ≥ 1 FCFA
                raise ServingError("Estimation non exploitable pour la comparaison.")

            market_response: ComparisonMarketResponse | None = None
            to_market_mean: GapResponse | None = None
            to_market_median: GapResponse | None = None
            if group is not None:
                if (
                    group.neighborhood is None
                    or group.property_type is None
                    or group.bedrooms is None
                ):
                    # Les filtres exacts garantissent ces dimensions : un groupe
                    # incomplet signalerait une réponse de marché incohérente.
                    raise ServingError(
                        "Groupe de marché incomplet pour la comparaison."
                    )
                market_response = ComparisonMarketResponse(
                    city=group.city,
                    neighborhood=group.neighborhood,
                    property_type=group.property_type,
                    bedrooms=group.bedrooms,
                    n_observations=group.stats.n_observations,
                    mean_rent_price=group.stats.mean_rent_price,
                    median_rent_price=group.stats.median_rent_price,
                    median_published=group.stats.median_published,
                    quality=group.quality,
                )
                to_market_mean = _gap(listing.asking_rent, group.stats.mean_rent_price)
                to_market_median = _gap(listing.asking_rent, group.stats.median_rent_price)

            items.append(
                ComparisonItemResponse(
                    listing=listing,
                    estimate=ComparisonEstimateResponse(
                        estimated_rent=prediction.estimated_rent,
                        lower_bound=prediction.lower_bound,
                        upper_bound=prediction.upper_bound,
                    ),
                    market=market_response,
                    gaps=ComparisonGapsResponse(
                        to_estimate=to_estimate,
                        to_market_mean=to_market_mean,
                        to_market_median=to_market_median,
                    ),
                )
            )

        if len(model_versions) != 1:
            # Une seule version est annoncée en tête de réponse : mélanger deux
            # versions rendrait l'étiquette mensongère.
            raise ServingError("Versions de modèle hétérogènes dans une comparaison.")

        return ComparisonResponse(
            currency=currency,
            min_publish_n=min_publish_n,
            model_version=model_versions.pop(),
            comparisons=items,
        )


def _gap(asking_rent: int, reference: int | None) -> GapResponse | None:
    """Écart signé et relatif ; `None` si la référence n'est pas disponible.

    Une référence non publiée (médiane sous le seuil) ou un groupe absent ne
    produit pas un écart : aucun zéro trompeur, aucune division par zéro.
    """
    if reference is None or reference <= 0:
        return None
    absolute = asking_rent - reference
    return GapResponse(
        absolute=absolute,
        relative_pct=round(100 * absolute / reference, 1),
    )
