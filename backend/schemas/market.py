"""Contrat de réponse des endpoints de marché (ticket #53, spec 08 §3).

Trois formes, une seule règle : **aucune statistique sans son nombre
d'observations**, aucune médiane publiée sous le seuil (`min_publish_n`), et les
données imparfaites (prix bornés, republications, quartiers non reconnus) sont
exposées avec leur volume plutôt que masquées.

Les statistiques viennent des marts dbt ; l'API ne recalcule aucun agrégat. La
seule opération de synthèse est la moyenne pondérée du niveau quartier, qui est
exacte à partir des moyennes et effectifs des groupes (voir
`backend/repositories/market.py`).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class MarketStatsResponse(BaseModel):
    """Statistiques d'un groupe, avec leur fourchette p10/p90 et leur N."""

    n_observations: int = Field(ge=0, description="Nombre d'observations du groupe.")
    mean_rent_price: int = Field(ge=0, description="Loyer demandé moyen (FCFA).")
    median_rent_price: int | None = Field(
        default=None,
        description=(
            "Médiane du loyer demandé (FCFA) ; `null` sous le seuil de publication "
            "(`min_publish_n`). Voir `median_published`."
        ),
    )
    median_published: bool = Field(
        description="`true` seulement si la médiane est publiée (N ≥ `min_publish_n`)."
    )
    p10_rent_price: int | None = Field(
        default=None, description="10ᵉ centile du loyer demandé (FCFA)."
    )
    p90_rent_price: int | None = Field(
        default=None, description="90ᵉ centile du loyer demandé (FCFA)."
    )
    min_rent_price: int = Field(ge=0, description="Loyer demandé minimum observé (FCFA).")
    max_rent_price: int = Field(ge=0, description="Loyer demandé maximum observé (FCFA).")


class NeighborhoodStatsResponse(BaseModel):
    """Synthèse agrégeable d'un quartier (sans médiane ni centiles)."""

    n_observations: int = Field(ge=0, description="Nombre d'observations du quartier.")
    mean_rent_price: int = Field(
        ge=0, description="Loyer demandé moyen du quartier (moyenne pondérée par groupe)."
    )
    min_rent_price: int = Field(ge=0, description="Loyer demandé minimum observé (FCFA).")
    max_rent_price: int = Field(ge=0, description="Loyer demandé maximum observé (FCFA).")


class MarketQualityResponse(BaseModel):
    """Biais connus du groupe, avec leur volume et leur part.

    Ces champs ne sont pas des défauts à corriger à l'affichage : ils indiquent
    au client ce que la statistique contient réellement (prix « à partir de »,
    annonces republiées, libellés de quartier non reconnus).
    """

    n_price_bound: int = Field(ge=0, description="Observations dont le prix est une borne.")
    pct_price_bound: float = Field(ge=0, le=100, description="Part de prix bornés (%).")
    n_republication: int = Field(ge=0, description="Observations republiées.")
    pct_republication: float = Field(ge=0, le=100, description="Part de republications (%).")
    n_neighborhood_unrecognized: int | None = Field(
        default=None,
        description="Observations sur un quartier non reconnu (niveau ville uniquement).",
    )
    pct_neighborhood_unrecognized: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Part d'observations sur un quartier non reconnu (niveau ville uniquement).",
    )


class ObservedPeriodResponse(BaseModel):
    """Fenêtre réellement couverte par les données de marché."""

    start: date | None = Field(default=None, description="Première date observée.")
    end: date | None = Field(default=None, description="Dernière date observée.")


class CityMarketResponse(BaseModel):
    """Statistiques d'une ville."""

    city: str = Field(description="Ville canonique (`Douala` ou `Yaoundé`).")
    stats: MarketStatsResponse
    quality: MarketQualityResponse


class NeighborhoodMarketResponse(BaseModel):
    """Synthèse d'un quartier d'une ville."""

    neighborhood: str = Field(description="Quartier tel qu'annoncé.")
    neighborhood_recognized: bool = Field(
        description="`false` si le libellé n'est pas reconnu par le référentiel."
    )
    n_groups: int = Field(
        ge=0, description="Nombre de groupes (type × chambres) composant la synthèse."
    )
    stats: NeighborhoodStatsResponse
    quality: MarketQualityResponse


class PriceGroupResponse(BaseModel):
    """Statistiques d'un groupe de marché, au grain réellement disponible."""

    city: str = Field(description="Ville du groupe.")
    neighborhood: str | None = Field(
        default=None, description="Quartier du groupe ; `null` pour une statistique de ville."
    )
    neighborhood_recognized: bool | None = Field(
        default=None, description="Reconnaissance du quartier ; `null` sans quartier."
    )
    property_type: str | None = Field(
        default=None, description="Type de bien ; `null` si le filtre ne s'applique pas."
    )
    bedrooms: int | None = Field(
        default=None, description="Nombre de chambres ; `null` si le filtre ne s'applique pas."
    )
    stats: MarketStatsResponse
    quality: MarketQualityResponse


class CitiesResponse(BaseModel):
    """Villes disponibles et leurs statistiques agrégées."""

    currency: Literal["XAF"] = Field(description="Devise unique du projet (FCFA).")
    min_publish_n: int = Field(
        ge=1, description="Seuil de publication des médianes (nombre d'observations)."
    )
    observed_period: ObservedPeriodResponse
    cities: list[CityMarketResponse]


class NeighborhoodsResponse(BaseModel):
    """Quartiers d'une ville, avec leur volume d'observations."""

    currency: Literal["XAF"] = Field(description="Devise unique du projet (FCFA).")
    min_publish_n: int = Field(
        ge=1, description="Seuil de publication appliqué aux groupes de `/market/prices`."
    )
    observed_period: ObservedPeriodResponse
    city: str = Field(description="Ville interrogée.")
    n_observations: int = Field(ge=0, description="Total des observations des quartiers retournés.")
    n_neighborhoods: int = Field(ge=0, description="Nombre de quartiers retournés.")
    neighborhoods: list[NeighborhoodMarketResponse]


class PricesResponse(BaseModel):
    """Groupes de prix correspondant aux filtres, avec leur N et leur qualité."""

    currency: Literal["XAF"] = Field(description="Devise unique du projet (FCFA).")
    min_publish_n: int = Field(
        ge=1, description="Seuil de publication des médianes (nombre d'observations)."
    )
    observed_period: ObservedPeriodResponse
    n_observations: int = Field(
        ge=0, description="Total des observations des groupes retournés (jamais omis)."
    )
    groups: list[PriceGroupResponse]
