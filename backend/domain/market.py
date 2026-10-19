"""Objets du marché et règle de publication des médianes.

Ces objets décrivent ce que les marts de marché exposent **déjà** : ils ne
recalculent aucune statistique. Le seuil de publication est une règle du domaine,
alignée sur la variable dbt `min_publish_n` (défaut 30, décision Phase 3) : une
médiane n'est jamais exposée sous ce seuil, même si un mart la fournissait par
erreur. Le service applique donc ce seuil **en plus** du filtre dbt — défense en
profondeur, jamais une médiane inventée.

Le seuil backend est une **borne basse** : si le mart était construit avec un
seuil dbt plus élevé, ses médianes seraient déjà nulles ; s'il était construit
avec un seuil plus bas, le backend masquerait les médianes entre les deux. Aucun
cas ne publie une médiane sous 30 observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

MIN_PUBLISH_N: Final[int] = 30

CURRENCY: Final[str] = "XAF"


@dataclass(frozen=True, slots=True)
class MarketStats:
    """Statistiques d'un groupe de marché, toujours accompagnées de leur N."""

    n_observations: int
    mean_rent_price: int
    median_rent_price: int | None
    p10_rent_price: int | None
    p90_rent_price: int | None
    min_rent_price: int
    max_rent_price: int


@dataclass(frozen=True, slots=True)
class NeighborhoodStats:
    """Synthèse d'un quartier : seules les valeurs agrégeables sans erreur.

    Ni médiane ni centiles : agréger des médianes de sous-groupes ne donne pas
    la médiane du quartier. Le détail par (type, chambres) est exposé par
    ``/market/prices``, où le seuil de publication s'applique.
    """

    n_observations: int
    mean_rent_price: int
    min_rent_price: int
    max_rent_price: int


@dataclass(frozen=True, slots=True)
class MarketQuality:
    """Données imparfaites **quantifiées**, jamais masquées (invariant 8)."""

    n_price_bound: int
    pct_price_bound: float
    n_republication: int
    pct_republication: float
    n_neighborhood_unrecognized: int | None = None
    pct_neighborhood_unrecognized: float | None = None


@dataclass(frozen=True, slots=True)
class CityMarket:
    """Statistiques d'une ville (grain ``mart_city_prices``)."""

    city: str
    stats: MarketStats
    quality: MarketQuality


@dataclass(frozen=True, slots=True)
class NeighborhoodMarket:
    """Synthèse d'un quartier, construite depuis ``mart_neighborhood_prices``."""

    city: str
    neighborhood: str
    neighborhood_recognized: bool
    n_groups: int
    stats: NeighborhoodStats
    quality: MarketQuality


@dataclass(frozen=True, slots=True)
class PriceGroup:
    """Groupe de prix au grain le plus fin disponible.

    Les dimensions absentes du niveau interrogé sont nulles : une statistique
    de ville n'a ni quartier, ni type, ni nombre de chambres.
    """

    city: str
    neighborhood: str | None
    neighborhood_recognized: bool | None
    property_type: str | None
    bedrooms: int | None
    stats: MarketStats
    quality: MarketQuality


@dataclass(frozen=True, slots=True)
class ObservationPeriod:
    """Fenêtre réellement couverte par les observations (dates min/max)."""

    start: date | None
    end: date | None
