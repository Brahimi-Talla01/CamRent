"""Tests des fonctions d'extraction et de normalisation (Phase 2)."""

from __future__ import annotations

from pipelines.parsing import (
    normalize_property_type,
    parse_area_m2,
    parse_price,
    parse_rooms,
    parse_yes_no,
)


def test_parse_price_exact() -> None:
    assert parse_price("CFA  500,000") == (500000, False)
    assert parse_price("230 000 FCFA") == (230000, False)
    assert parse_price("150000") == (150000, False)


def test_parse_price_bound() -> None:
    assert parse_price("> 120 000 FCFA") == (120000, True)
    assert parse_price("≥ 100 000 FCFA") == (100000, True)


def test_parse_price_missing() -> None:
    assert parse_price("Contactez le vendeur") == (None, False)
    assert parse_price("") == (None, False)


def test_parse_rooms() -> None:
    assert parse_rooms("3 Chambres") == (3, False)
    assert parse_rooms("2 Salles de bain") == (2, False)
    assert parse_rooms("> 3 bedrooms") == (3, True)


def test_normalize_property_type() -> None:
    assert normalize_property_type("Appartement à louer à Akwa") == "apartment"
    assert normalize_property_type("3 bedrooms apartment to rent") == "apartment"
    assert normalize_property_type("Studio moderne") == "studio"
    assert normalize_property_type("Maison à louer") == "house"
    assert normalize_property_type("n'importe quoi") == "unknown"


def test_parse_area() -> None:
    assert parse_area_m2("Surface: 110 m2") == 110.0
    assert parse_area_m2("aucune surface") is None


def test_parse_yes_no() -> None:
    assert parse_yes_no("with parking") is True
    assert parse_yes_no("sans parking") is False
    assert parse_yes_no("peut-être") is None
