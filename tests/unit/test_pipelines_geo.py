"""Tests de la résolution ville / quartier."""

from __future__ import annotations

from pipelines.geo import resolve_city, resolve_neighborhood


def test_resolve_city() -> None:
    assert resolve_city("Douala") == "Douala"
    assert resolve_city("YAOUNDE") == "Yaoundé"
    assert resolve_city("Douala/Littoral") == "Douala"
    assert resolve_city("Kribi") is None


def test_resolve_neighborhood_exact() -> None:
    assert resolve_neighborhood("Akwa", "Douala") == ("Akwa", True)
    assert resolve_neighborhood("Bonamoussadi", "Douala") == ("Bonamoussadi", True)
    assert resolve_neighborhood("Bastos", "Yaoundé") == ("Bastos", True)


def test_resolve_neighborhood_variants() -> None:
    assert resolve_neighborhood("bonamoussadi", "Douala") == ("Bonamoussadi", True)
    assert resolve_neighborhood("Akwa nord", "Douala") == ("Akwa", True)
    assert resolve_neighborhood("Quartier Logpom", "Douala") == ("Logpom", True)


def test_resolve_neighborhood_fuzzy() -> None:
    canonical, recognized = resolve_neighborhood("Bonamousadi", "Douala")
    assert (canonical, recognized) == ("Bonamoussadi", True)


def test_resolve_neighborhood_unknown() -> None:
    canonical, recognized = resolve_neighborhood("Village Introuvable", "Douala")
    assert recognized is False
    assert canonical == "Village Introuvable"
