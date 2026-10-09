"""Tests de parsing des collecteurs (fixtures HTML inline, aucun réseau)."""

from __future__ import annotations

from ingestion.sources.geloka import parse_barometer
from ingestion.sources.koutchoumi import detail_links, parse_detail

GELOKA_HTML = """
<html><body>
<p>À Douala, le loyer médian d'un appartement est de 300 000 FCFA par mois
(8 octobre 2026), dans une fourchette de 60 000 à 1 500 000 FCFA, sur 32 annonces
analysées par Geloka.</p>
<p>À Yaoundé, le loyer médian d'un studio est de 65 000 FCFA par mois
(8 octobre 2026), dans une fourchette de 45 000 à 120 000 FCFA, sur 15 annonces
analysées par Geloka.</p>
</body></html>
"""

KOUTCHOUMI_HTML = """<html><body>
<div>Apartment to rent in Bali, Douala</div>
<div>Quartier: Bali</div>
<div>Bedrooms: 2</div>
<div>Bathrooms: 3</div>
<div>Surface: 110 m2</div>
</body></html>"""

KOUTCHOUMI_URL = (
    "https://www.koutchoumi.com/en/124892/"
    "apartment-to-rent-douala-bali-sgc-1-living-room-s-2-bedroom-s-3-bathroom-s-850-000-fcfa-month"
)


def test_geloka_parse_barometer() -> None:
    records = list(parse_barometer(GELOKA_HTML, "https://www.geloka.com/fr/rent-barometer"))
    assert len(records) == 2

    douala = records[0]
    assert douala.source == "geloka"
    assert douala.fields["city_text"] == "Douala"
    assert douala.fields["property_type_text"] == "appartement"
    assert douala.fields["rent_price"] == 300000
    assert douala.fields["sample_size"] == 32

    yaounde = records[1]
    assert yaounde.fields["city_text"] == "Yaoundé"
    assert yaounde.fields["property_type_text"] == "studio"
    assert yaounde.fields["rent_price"] == 65000


def test_koutchoumi_parse_detail() -> None:
    record = parse_detail(KOUTCHOUMI_URL, KOUTCHOUMI_HTML)
    assert record is not None
    assert record.source == "koutchoumi"
    assert record.source_listing_id == "124892"
    assert record.fields["price_text"] == "850 000 FCFA"  # extrait du slug
    assert record.fields["neighborhood_text"] == "Bali"
    assert record.fields["bedrooms_text"] == "2"
    assert record.fields["bathrooms_text"] == "3"
    assert record.fields["area_text"] == "110 m2"
    assert str(record.fields["slug"]).startswith("apartment-to-rent")


def test_koutchoumi_parse_detail_rejects_category_url() -> None:
    category = "https://www.koutchoumi.com/apartments-to-rent-at-douala-cameroon.html"
    assert parse_detail(category, "<html></html>") is None


def test_koutchoumi_detail_links() -> None:
    html = (
        '<a href="/en/124892/some-slug">x</a>'
        '<a href="/fr/123/truc">y</a>'
        '<a href="/en/main/showResults">z</a>'
    )
    links = detail_links(html)
    assert links == [
        "https://www.koutchoumi.com/en/124892/some-slug",
        "https://www.koutchoumi.com/fr/123/truc",
    ]
