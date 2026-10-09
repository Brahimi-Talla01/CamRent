"""Tests des adaptateurs et de la construction du Silver dataset."""

from __future__ import annotations

import pytest

from pipelines import config, silver


def _koutchoumi_live(listing_id: str, title: str, slug: str, price_text: str) -> dict:
    return {
        "source": "koutchoumi",
        "source_listing_id": listing_id,
        "url": f"https://www.koutchoumi.com/en/{listing_id}/{slug}",
        "collected_at": "2026-10-09T06:00:00+00:00",
        "posted_at": None,
        "fields": {"slug": slug, "title": title, "price_text": price_text},
        "raw_text": "",
    }


def _jumia(listing_id: str) -> dict:
    return {
        "source": "reference_local",
        "source_listing_id": listing_id,
        "url": "file://jumia.csv",
        "collected_at": "2026-10-09T06:00:00+00:00",
        "posted_at": None,
        "fields": {
            "source_file": "jumia.csv",
            "Address": "Akwa, Akwa, Douala, Littoral",
            "Bathrooms": "2 Salles de bain",
            "Bedrooms": "3 Chambres",
            "Designation": "Appartement à louer à Akwa",
            "Price": "CFA  500,000",
        },
        "raw_text": "",
    }


def _koutchoumi_file(listing_id: str) -> dict:
    return {
        "source": "reference_local",
        "source_listing_id": listing_id,
        "url": "file://koutchoumi1.csv",
        "collected_at": "2026-10-09T06:00:00+00:00",
        "posted_at": None,
        "fields": {
            "source_file": "koutchoumi1.csv",
            "Area": "Douala/Logpom",
            "Bathrooms": "> 2 bathrooms",
            "Bedrooms": "> 3 bedrooms",
            "Price": "> 120 000 FCFA",
            "Type": "3 bedrooms apartment to rent",
        },
        "raw_text": "",
    }


def test_build_maps_live_koutchoumi() -> None:
    slug = "studio-to-rent-douala-bonapriso-rue-njo-njo-230-000-fcfa-month"
    title = "Studio to rent at Douala, Bonapriso - 230 000 FCFA"
    result = silver.build([_koutchoumi_live("124295", title, slug, "230 000 FCFA")])

    assert result.stats["silver_rows"] == 1
    row = result.silver[0]
    assert row["city"] == "Douala"
    assert row["neighborhood"] == "Bonapriso"
    assert row["property_type"] == "studio"
    assert row["rent_price"] == 230000


def test_build_maps_local_jumia() -> None:
    result = silver.build([_jumia("jumia-000000")])
    row = result.silver[0]
    assert row["city"] == "Douala"
    assert row["neighborhood"] == "Akwa"
    assert row["property_type"] == "apartment"
    assert row["bedrooms"] == 3
    assert row["bathrooms"] == 2
    assert row["rent_price"] == 500000


def test_build_flags_bound_values() -> None:
    result = silver.build([_koutchoumi_file("koutchoumi1-000000")])
    row = result.silver[0]
    assert row["neighborhood"] == "Logpom"
    assert row["rent_price"] == 120000
    assert row["price_is_bound"] is True
    assert row["bedrooms_is_bound"] is True
    assert row["bathrooms_is_bound"] is True


def test_technical_duplicate_removed() -> None:
    slug = "studio-to-rent-douala-bonapriso-x-100-000-fcfa-month"
    title = "Studio to rent at Douala, Bonapriso - 100 000 FCFA"
    record = _koutchoumi_live("999", title, slug, "100 000 FCFA")
    result = silver.build([record, dict(record)])
    assert result.stats["silver_rows"] == 1
    assert result.stats["reasons"]["doublon_technique"] == 1


def test_missing_price_goes_to_quarantine() -> None:
    slug = "studio-to-rent-douala-akwa-contact-fcfa-month"
    title = "Studio to rent at Douala, Akwa - Contactez le vendeur"
    result = silver.build([_koutchoumi_live("1", title, slug, "Contactez le vendeur")])
    assert result.stats["silver_rows"] == 0
    assert result.quarantine[0]["quarantine_reason"] == "prix_manquant"


def test_extreme_price_is_flagged_not_removed() -> None:
    slug = "villa-to-rent-douala-bonapriso-9-000-000-fcfa-month"
    title = "Villa to rent at Douala, Bonapriso - 9 000 000 FCFA"
    result = silver.build([_koutchoumi_live("7", title, slug, "9 000 000 FCFA")])
    assert result.stats["silver_rows"] == 1
    assert "price_outlier" in result.silver[0]["outlier_flags"]


def test_write_outputs_columns(tmp_path) -> None:
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")

    result = silver.build([_jumia("jumia-000000")])
    paths = silver.write_outputs(result, tmp_path)

    assert paths["silver"].exists()
    assert paths["quarantine"].exists()
    frame = pd.read_parquet(paths["silver"])
    assert list(frame.columns) == list(config.SILVER_COLUMNS)
