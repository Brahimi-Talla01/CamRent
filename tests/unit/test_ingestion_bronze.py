"""Tests des validations Bronze (présence, format, volume, métadonnées, fraîcheur)."""

from __future__ import annotations

from ingestion import bronze, config, storage
from ingestion.models import RawRecord


def _write_lot(monkeypatch, tmp_path, source: str) -> storage.RawJsonlWriter:
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    spec = config.SOURCES[source]
    writer = storage.RawJsonlWriter(category=spec.category, source=spec.name)
    writer.write(RawRecord(source=spec.name, source_listing_id="1", url="http://x"))
    writer.close()
    storage.write_metadata(spec, writer, list(spec.urls))
    return writer


def test_bronze_passes_with_a_complete_lot(monkeypatch, tmp_path) -> None:
    _write_lot(monkeypatch, tmp_path, "koutchoumi")
    report = bronze.run_validations()
    assert report.ok, report.failures


def test_bronze_fails_when_no_raw(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    report = bronze.run_validations()
    assert not report.ok
    assert any(check.name == "présence" for check in report.checks)


def test_bronze_flags_missing_metadata(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    writer = storage.RawJsonlWriter(category=config.CATEGORY_LISTINGS, source="koutchoumi")
    writer.write(RawRecord(source="koutchoumi", source_listing_id="1", url="http://x"))
    writer.close()

    report = bronze.run_validations()
    assert not report.ok
    assert any(check.name == "métadonnées" and not check.ok for check in report.checks)


def test_bronze_flags_invalid_json(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    writer = storage.RawJsonlWriter(category=config.CATEGORY_LISTINGS, source="koutchoumi")
    writer.write(RawRecord(source="koutchoumi", source_listing_id="1", url="http://x"))
    writer.close()
    with writer.path.open("a", encoding="utf-8") as handle:
        handle.write("{ceci n'est pas du json}\n")

    report = bronze.run_validations()
    assert any(check.name == "format JSON" and not check.ok for check in report.checks)
