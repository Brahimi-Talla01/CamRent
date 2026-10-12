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


def test_resolve_neighborhood_issue20_douala() -> None:
    # Sous-quartiers d'Akwa et variante « Cité UBO » (issue #20).
    assert resolve_neighborhood("Akwa I", "Douala") == ("Akwa", True)
    assert resolve_neighborhood("Akwa II", "Douala") == ("Akwa", True)
    assert resolve_neighborhood("Cite Ubo Palmiers", "Douala") == (
        "Cité des Palmiers",
        True,
    )
    # Quartiers doualais ajoutés au seed (variantes de casse/accents incluses).
    assert resolve_neighborhood("Malangue", "Douala") == ("Malangue", True)
    assert resolve_neighborhood("Logbaba", "Douala") == ("Logbaba", True)
    assert resolve_neighborhood("Bessengué", "Douala") == ("Bessengue", True)
    assert resolve_neighborhood("Cité Sic", "Douala") == ("Cité SIC", True)
    assert resolve_neighborhood("Bonatéki", "Douala") == ("Bonateki", True)
    assert resolve_neighborhood("Ngangué", "Douala") == ("Ngangue", True)
    assert resolve_neighborhood("Youpwe", "Douala") == ("Youpwé", True)
    # Descriptions d'annonces nommant explicitement un quartier canonique.
    assert resolve_neighborhood("TERMINUS BONAMOUSSADI", "Douala") == (
        "Bonamoussadi",
        True,
    )
    assert resolve_neighborhood("RUE KOTTO", "Douala") == ("Kotto", True)


def test_resolve_neighborhood_issue20_yaounde() -> None:
    assert resolve_neighborhood("CITEE VERTE", "Yaoundé") == ("Cité Verte", True)
    assert resolve_neighborhood("Oyom Abang", "Yaoundé") == ("Oyom-Abang", True)
    assert resolve_neighborhood("SIMBOCK TRADEX", "Yaoundé") == ("Simbock", True)
    assert resolve_neighborhood("Obobogo", "Yaoundé") == ("Obobogo", True)
    assert resolve_neighborhood("Montée jouvence", "Yaoundé") == ("Jouvence", True)
    assert resolve_neighborhood("BASTOS (GOLF)", "Yaoundé") == ("Bastos", True)


def test_resolve_neighborhood_ambiguous_stays_unknown() -> None:
    # « Elig » désigne plusieurs quartiers de Yaoundé (Elig-Essono, Elig-Edzoa,
    # Elig-Effa) : aucun mapping n'est inventé, la valeur reste non reconnue.
    canonical, recognized = resolve_neighborhood("Elig", "Yaoundé")
    assert recognized is False
    assert canonical == "Elig"
    # « CAMP SIC » (Yaoundé) ne doit pas être confondu avec « Cité SIC » (Douala).
    assert resolve_neighborhood("CAMP SIC", "Yaoundé")[1] is False
