"""Contrat de l'endpoint de comparaison (ticket #54, spec 08 §4).

Le logement observé reprend **exactement** les champs de `PredictionRequest`
(ville, quartier, type, chambres, salles de bain), plus le prix demandé. Les
champs non collectés restent refusés par héritage (`extra="forbid"`).

Le groupe de marché est celui du grain réellement exposé par les marts :
(ville, quartier, type, chambres). Les salles de bain servent à l'estimation,
mais **pas** au groupe de comparaison : les marts n'exposent pas ce grain, et
inventer une référence plus fine donnerait un N trompeur.

L'écart est signé : `asking_rent - référence`. Un écart positif signifie que le
prix demandé est **au-dessus** de la référence. Aucun score de confiance, aucune
recommandation : le produit informe, il ne certifie pas une valeur.
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from .market import MarketQualityResponse
from .prediction import PredictionRequest

# Borne technique : la spec 09 compare quelques logements (2+), pas un lot
# illimité. Elle évite qu'une requête déclenche un nombre non borné de
# prédictions et de lectures SQL.
MAX_LISTINGS: Final[int] = 10


class ComparisonListingRequest(PredictionRequest):
    """Logement à comparer : caractéristiques du modèle + prix demandé."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "city": "Douala",
                "neighborhood": "Bonamoussadi",
                "property_type": "apartment",
                "bedrooms": 2,
                "bathrooms": 2,
                "asking_rent": 150000,
            }
        },
    )

    asking_rent: int = Field(
        ge=1,
        description=(
            "Loyer mensuel **demandé** dans l'annonce, en FCFA (prix affiché, pas "
            "le loyer effectivement payé)."
        ),
    )


class ComparisonRequest(BaseModel):
    """Un ou plusieurs logements à confronter au marché local."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "listings": [
                    {
                        "city": "Douala",
                        "neighborhood": "Bonamoussadi",
                        "property_type": "apartment",
                        "bedrooms": 2,
                        "bathrooms": 2,
                        "asking_rent": 150000,
                    }
                ]
            }
        },
    )

    listings: list[ComparisonListingRequest] = Field(
        min_length=1,
        max_length=MAX_LISTINGS,
        description=(
            "Logements à comparer, dans l'ordre de la réponse. Un seul logement "
            "répond à « ce prix est-il au-dessus du marché ? » ; deux ou plus "
            "alimentent l'écran « comparer »."
        ),
    )


class GapResponse(BaseModel):
    """Écart signé entre le prix demandé et une référence."""

    absolute: int = Field(
        description="Écart en FCFA : `asking_rent - référence` (positif = au-dessus)."
    )
    relative_pct: float | None = Field(
        default=None,
        description=(
            "Écart relatif en % : `100 × (asking_rent - référence) / référence`, "
            "arrondi à une décimale. `null` seulement si la référence n'est pas "
            "publiée."
        ),
    )


class ComparisonEstimateResponse(BaseModel):
    """Estimation du modèle épinglé pour ce logement."""

    estimated_rent: int = Field(ge=1, description="Loyer demandé estimé (FCFA).")
    lower_bound: int = Field(ge=1, description="Borne basse calibrée 5 % (FCFA).")
    upper_bound: int = Field(ge=1, description="Borne haute calibrée 95 % (FCFA).")


class ComparisonMarketResponse(BaseModel):
    """Référence locale : groupe de marché, volume, moyenne et médiane.

    Le groupe est explicite pour que le client sache **à quoi** le logement est
    comparé. Ses dimensions sont celles du mart : ville, quartier, type et
    chambres ; les salles de bain n'y entrent pas.
    """

    city: str = Field(description="Ville du groupe de comparaison.")
    neighborhood: str = Field(description="Quartier du groupe de comparaison.")
    property_type: str = Field(description="Type de bien du groupe.")
    bedrooms: int = Field(description="Nombre de chambres du groupe.")
    n_observations: int = Field(
        ge=0, description="Nombre d'observations du groupe (jamais omis)."
    )
    mean_rent_price: int = Field(ge=0, description="Loyer demandé moyen du groupe (FCFA).")
    median_rent_price: int | None = Field(
        default=None,
        description="Médiane du groupe (FCFA) ; `null` sous le seuil de publication.",
    )
    median_published: bool = Field(
        description="`true` seulement si la médiane est publiée (N ≥ `min_publish_n`)."
    )
    quality: MarketQualityResponse


class ComparisonGapsResponse(BaseModel):
    """Écarts du prix demandé aux trois références disponibles."""

    to_estimate: GapResponse = Field(
        description="Écart à l'estimation du modèle (toujours calculable)."
    )
    to_market_mean: GapResponse | None = Field(
        default=None, description="Écart à la moyenne locale ; `null` sans groupe."
    )
    to_market_median: GapResponse | None = Field(
        default=None,
        description="Écart à la médiane locale ; `null` sans groupe ou médiane non publiée.",
    )


class ComparisonItemResponse(BaseModel):
    """Comparaison d'un logement : prix demandé, estimation, marché, écarts."""

    listing: ComparisonListingRequest
    estimate: ComparisonEstimateResponse
    market: ComparisonMarketResponse | None = Field(
        default=None,
        description=(
            "Référence locale ; `null` si le mart n'a aucun groupe pour cette "
            "combinaison. Aucune référence plus large n'est inventée."
        ),
    )
    gaps: ComparisonGapsResponse


class ComparisonResponse(BaseModel):
    """Réponse de `POST /api/v1/comparisons`."""

    currency: Literal["XAF"] = Field(description="Devise unique du projet (FCFA).")
    min_publish_n: int = Field(
        ge=1, description="Seuil de publication appliqué à la médiane locale."
    )
    model_version: str = Field(
        description="Version du modèle épinglé utilisée pour toutes les estimations."
    )
    comparisons: list[ComparisonItemResponse] = Field(
        description="Une entrée par logement fourni, dans l'ordre de la requête."
    )
