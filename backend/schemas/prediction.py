"""Schémas d'entrée de l'API publique.

Le contrat est **strict** : un champ que la plateforme data ne collecte pas
(`area_m2`, `parking`, `gated`, `furnished`) est refusé (`extra="forbid"`) et non
silencieusement ignoré. Accepter un champ que le modèle n'utilise pas laisserait
croire que l'estimation en tient compte (spec 08 §Scope Limits, décision 6 « on
finalise le MVP d'abord »).
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from ..domain import vocabulary

# Un quartier est une chaîne libre côté annonce : on retire les espaces superflus et
# on refuse une valeur vide, sans transformer le libellé (la reconnaissance du
# quartier est vérifiée par le service d'estimation, ticket #51).
Neighborhood = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=vocabulary.NEIGHBORHOOD_MAX_LENGTH,
    ),
]

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
