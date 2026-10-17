"""Vocabulaire du domaine, aligné sur les valeurs réellement présentes.

Ces vocabulaires **ferment** l'entrée de l'API publique : une ville ou un type de
bien absent des données ne peut pas être estimé, et le refuser en entrée vaut mieux
que renvoyer une estimation inventée (spec 08, §Scope Limits).

Provenance (état constaté le 2026-10-17 sur `analytics_marts.mart_ml_dataset`) :

- villes : Douala (2 811 observations), Yaoundé (181) — MVP de la décision du
  2026-10-15, Conakry restant un chantier séparé ;
- types de biens normalisés au Silver : `apartment` (2 903), `studio` (73),
  `room` (15), `house` (1) ;
- bornes de pièces : 0 à 10, déjà appliquées par la plateforme data
  (`pipelines/config.py::ROOMS_MAX_PLAUSIBLE`, borne haute des tests dbt
  `within_range`) — au-delà, les valeurs sont **signalées** en `outlier_flags` et ne
  doivent jamais être demandées à l'API.

Ce module ne doit pas dériver des données : le ticket #53 (endpoints de marché)
ajoute le test de cohérence entre ce vocabulaire et les marts.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

CITIES: Final[tuple[str, ...]] = ("Douala", "Yaoundé")

PROPERTY_TYPES: Final[tuple[str, ...]] = ("apartment", "studio", "room", "house")

# Bornes de pièces (chambres, salles de bain), identiques à celles de la plateforme data.
ROOMS_MIN: Final[int] = 0
ROOMS_MAX: Final[int] = 10

NEIGHBORHOOD_MAX_LENGTH: Final[int] = 120

# Enums construits depuis les tuples ci-dessus (source unique) : les valeurs sont
# conservées telles quelles (`type=str` évite la mise en minuscules de `StrEnum`), ce
# qui permet de les comparer directement aux colonnes des marts.
CityName = Enum("CityName", {city: city for city in CITIES}, type=str, module=__name__)
PropertyType = Enum(
    "PropertyType", {kind: kind for kind in PROPERTY_TYPES}, type=str, module=__name__
)
