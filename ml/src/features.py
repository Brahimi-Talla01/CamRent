"""Construction des features (Phase 6).

Feature engineering honnête par rapport aux données disponibles :

- **directes** : `bedrooms`, `bathrooms` (seules disponibles — `area_m2`,
  `furnished`, `parking`, `gated` sont vides dans le Silver, cf. Phase 3) ;
- **géographiques** : `city`, `neighborhood` (pas de latitude/longitude dans les
  données : impossible d'ajouter `distance_to_center`) ;
- **dérivées, sans leakage** : `total_pieces` (chambres + salles de bain) et
  `logements_dans_quartier` (profondeur de marché, **calculée sur l'entraînement
  uniquement**) ;
- **exclues** : `rent_per_m2` et toute statistique de prix ; les drapeaux de
  qualité (`price_is_bound`, `is_republication`, `outlier_flags`,
  `neighborhood_recognized`) restent hors du modèle — ils servent à décrire les
  scénarios, pas à prédire.

Les transformations qui apprennent des valeurs (comptages marché) sont encapsulées
dans un transformateur scikit-learn : elles sont donc ajustées **sur le seul
entraînement** et jamais sur la validation ou le test.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

CATEGORICAL_FEATURES: tuple[str, ...] = ("city", "neighborhood", "property_type")
NUMERIC_FEATURES: tuple[str, ...] = ("bedrooms", "bathrooms")
DERIVED_FEATURES: tuple[str, ...] = ("total_pieces", "logements_dans_quartier")
MODEL_FEATURES: tuple[str, ...] = CATEGORICAL_FEATURES + NUMERIC_FEATURES + DERIVED_FEATURES

# Colonnes volontairement écartées, avec la raison (reprise dans le rapport).
EXCLUDED_FEATURES: dict[str, str] = {
    "area_m2": "entièrement vide dans le Silver (Phase 3)",
    "furnished": "entièrement vide dans le Silver",
    "parking": "entièrement vide dans le Silver",
    "gated": "entièrement vide dans le Silver",
    "latitude": "absent des données collectées",
    "longitude": "absent des données collectées",
    "property_age": "aucune date de construction dans les annonces",
    "price_is_bound": "drapeau de qualité, pas une caractéristique du bien",
    "is_republication": "drapeau de qualité, pas une caractéristique du bien",
    "outlier_flags": "drapeau de qualité, pas une caractéristique du bien",
    "neighborhood_recognized": "drapeau de qualité, pas une caractéristique du bien",
    "rent_per_m2": "dérivée de la cible (data leakage, interdit)",
}


class MarketDepthEncoder(BaseEstimator, TransformerMixin):
    """Ajoute la profondeur de marché locale (`logements_dans_quartier`).

    Le comptage est appris **sur l'entraînement** et appliqué tel quel ensuite :
    un quartier absent de l'entraînement reçoit 0 (information explicite :
    le modèle n'a jamais vu ce quartier).
    """

    def __init__(self, keys: tuple[str, ...] = ("city", "neighborhood")) -> None:
        self.keys = keys

    def fit(self, frame: pd.DataFrame, y: Any = None) -> MarketDepthEncoder:
        counts = frame.groupby(list(self.keys), dropna=False).size()
        self.counts_: dict[tuple[Any, ...], int] = {
            self._as_tuple(key): int(value) for key, value in counts.items()
        }
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not hasattr(self, "counts_"):
            raise RuntimeError("MarketDepthEncoder doit être ajusté (`fit`) avant `transform`.")
        result = frame.copy()
        result["logements_dans_quartier"] = [
            self.counts_.get(self._as_tuple(key), 0)
            for key in zip(*(frame[key] for key in self.keys), strict=True)
        ]
        return result

    def _as_tuple(self, key: Any) -> tuple[Any, ...]:
        return key if isinstance(key, tuple) else (key,)


class FeatureBuilder(BaseEstimator, TransformerMixin):
    """Assemble les features du modèle à partir du mart ML.

    `fit` ne lit que les colonnes d'entrée et la complétude des chambres : aucune
    information de cible n'est utilisée, ce qui garantit l'absence de fuite.
    """

    def __init__(self, keys: tuple[str, ...] = ("city", "neighborhood")) -> None:
        self.keys = keys

    def fit(self, frame: pd.DataFrame, y: Any = None) -> FeatureBuilder:
        self.depth_ = MarketDepthEncoder(self.keys).fit(frame)
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        enriched = self.depth_.transform(frame)
        result = pd.DataFrame(index=enriched.index)
        for column in CATEGORICAL_FEATURES:
            result[column] = enriched[column].astype(str)
        for column in NUMERIC_FEATURES:
            result[column] = pd.to_numeric(enriched[column], errors="coerce")
        result["total_pieces"] = result["bedrooms"] + result["bathrooms"]
        result["logements_dans_quartier"] = enriched["logements_dans_quartier"].astype(float)
        return result
