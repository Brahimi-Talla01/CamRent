"""Schémas d'entrée de l'API publique.

Le contrat est **strict** : un champ que la plateforme data ne collecte pas
(`area_m2`, `parking`, `gated`, `furnished`) est refusé (`extra="forbid"`) et non
silencieusement ignoré. Accepter un champ que le modèle n'utilise pas laisserait
croire que l'estimation en tient compte (spec 08 §Scope Limits, décision 6 « on
finalise le MVP d'abord »).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..domain import vocabulary
from .common import Neighborhood

ROOMS_DESCRIPTION = (
    f"Nombre entier entre {vocabulary.ROOMS_MIN} et {vocabulary.ROOMS_MAX} "
    "(bornes déjà appliquées par la plateforme data)."
)


class PredictionRequest(BaseModel):
    """Caractéristiques réellement prises en charge par le modèle.

    Cinq champs sont demandés : les deux autres features du modèle (total de pièces,
    profondeur de marché du quartier) se déduisent des données, elles ne sont donc
    pas saisies par l'utilisateur.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "city": "Douala",
                "neighborhood": "Bonamoussadi",
                "property_type": "apartment",
                "bedrooms": 2,
                "bathrooms": 2,
            }
        },
    )

    city: vocabulary.CityName = Field(
        description="Ville du logement. MVP : Douala ou Yaoundé (Conakry est un chantier séparé)."
    )
    neighborhood: Neighborhood = Field(
        description="Quartier tel qu'annoncé ; sa reconnaissance est vérifiée côté service."
    )
    property_type: vocabulary.PropertyType = Field(
        description="Type de bien normalisé (valeurs réellement présentes dans les données)."
    )
    bedrooms: int = Field(
        ge=vocabulary.ROOMS_MIN,
        le=vocabulary.ROOMS_MAX,
        description=f"Chambres. {ROOMS_DESCRIPTION}",
    )
    bathrooms: int = Field(
        ge=vocabulary.ROOMS_MIN,
        le=vocabulary.ROOMS_MAX,
        description=f"Salles de bain. {ROOMS_DESCRIPTION}",
    )


class PredictionResponse(BaseModel):
    """Estimation indicative du loyer mensuel **demandé**, avec fourchette calibrée.

    L'estimation n'est jamais présentée comme la valeur officielle du bien : elle
    reflète les prix demandés dans les annonces (spec 08, invariant produit). Les
    bornes viennent de la régression quantile retenue en Phase 6 (5 % / 95 %),
    jamais d'un pourcentage appliqué à la prévision.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estimated_rent": 185000,
                "currency": "XAF",
                "lower_bound": 165000,
                "upper_bound": 205000,
                "model_version": "rent-model-v3",
            }
        }
    )

    estimated_rent: int = Field(
        ge=1, description="Loyer mensuel demandé estimé en FCFA (valeur indicative)."
    )
    currency: Literal["XAF"] = Field(description="Devise unique du projet (FCFA).")
    lower_bound: int = Field(
        ge=1,
        description=(
            "Borne basse de la fourchette calibrée (5ᵉ percentile, Phase 6), "
            "plancherée à 1 FCFA."
        ),
    )
    upper_bound: int = Field(
        ge=1, description="Borne haute de la fourchette calibrée (95ᵉ percentile, Phase 6)."
    )
    model_version: str = Field(
        description=(
            "Version du modèle épinglée (`ml/models/champion.json`), identique à chaque "
            "réponse tant que le pin ne change pas."
        )
    )
