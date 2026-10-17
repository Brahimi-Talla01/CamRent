"""Tests des schémas d'entrée de l'API publique (contrat strict).

Ce qui est vérifié ici est un invariant de produit, pas un détail d'implémentation :
l'API refuse un champ qu'elle ne sait pas traiter (`area_m2`, `parking`, `gated`,
`furnished`) au lieu de l'ignorer, et n'accepte que les villes et types de biens
réellement présents dans les données.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.domain import vocabulary
from backend.schemas.prediction import PredictionRequest

VALID_PAYLOAD: dict[str, object] = {
    "city": "Douala",
    "neighborhood": "Bonamoussadi",
    "property_type": "apartment",
    "bedrooms": 2,
    "bathrooms": 2,
}

# Champs volontairement exclus du MVP (non collectés par la plateforme data, décision 6).
NON_COLLECTED_FIELDS = ("area_m2", "parking", "gated", "furnished")


def test_valid_payload_is_accepted() -> None:
    request = PredictionRequest(**VALID_PAYLOAD)

    assert request.city == "Douala"
    assert request.bedrooms == 2


@pytest.mark.parametrize("field", NON_COLLECTED_FIELDS)
def test_non_collected_fields_are_refused(field: str) -> None:
    """Un champ que le modèle ignore est refusé, jamais ignoré silencieusement."""
    with pytest.raises(ValidationError) as exc_info:
        PredictionRequest(**VALID_PAYLOAD, **{field: 1})

    errors = exc_info.value.errors()
    assert [error["type"] for error in errors] == ["extra_forbidden"]
    assert [error["loc"] for error in errors] == [(field,)]


@pytest.mark.parametrize("city", ["Lyon", "douala", "Douala "])
def test_city_outside_the_vocabulary_is_refused(city: str) -> None:
    with pytest.raises(ValidationError):
        PredictionRequest(**{**VALID_PAYLOAD, "city": city})


@pytest.mark.parametrize("property_type", ["villa", "Apartment", "maison"])
def test_property_type_outside_the_vocabulary_is_refused(property_type: str) -> None:
    with pytest.raises(ValidationError):
        PredictionRequest(**{**VALID_PAYLOAD, "property_type": property_type})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("bedrooms", -1),
        ("bedrooms", vocabulary.ROOMS_MAX + 1),
        ("bathrooms", -1),
        ("bathrooms", 80),  # valeur observée en base, signalée en `outlier_flags`
    ],
)
def test_rooms_outside_project_bounds_are_refused(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        PredictionRequest(**{**VALID_PAYLOAD, field: value})


@pytest.mark.parametrize("value", [0, vocabulary.ROOMS_MAX])
def test_rooms_bounds_are_inclusive(value: int) -> None:
    """Les bornes du projet (0 à 10) sont inclusives, comme les tests dbt `within_range`."""
    request = PredictionRequest(**{**VALID_PAYLOAD, "bedrooms": value, "bathrooms": value})

    assert request.bedrooms == value


@pytest.mark.parametrize("neighborhood", ["", "   "])
def test_blank_neighborhood_is_refused(neighborhood: str) -> None:
    with pytest.raises(ValidationError):
        PredictionRequest(**{**VALID_PAYLOAD, "neighborhood": neighborhood})


def test_neighborhood_is_trimmed() -> None:
    request = PredictionRequest(**{**VALID_PAYLOAD, "neighborhood": "  Bonamoussadi  "})

    assert request.neighborhood == "Bonamoussadi"


@pytest.mark.parametrize("missing", sorted(VALID_PAYLOAD))
def test_missing_required_field_is_refused(missing: str) -> None:
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != missing}

    with pytest.raises(ValidationError):
        PredictionRequest(**payload)


def test_every_vocabulary_value_is_accepted() -> None:
    """Le vocabulaire et le schéma ne peuvent pas diverger sans faire échouer ce test."""
    for city in vocabulary.CITIES:
        for property_type in vocabulary.PROPERTY_TYPES:
            request = PredictionRequest(
                **{**VALID_PAYLOAD, "city": city, "property_type": property_type}
            )
            assert request.city == city
            assert request.property_type == property_type
