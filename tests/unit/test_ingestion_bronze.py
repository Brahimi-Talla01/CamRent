"""Tests des validations Bronze (présence, format, volume, métadonnées, fraîcheur)."""

from __future__ import annotations

import csv
import json

from ingestion import __main__ as ingestion_cli
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


def test_check_lot_passes_without_metadata(monkeypatch, tmp_path) -> None:
    """À la collecte, le lot est validé avant l'écriture des métadonnées."""
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    spec = config.SOURCES["koutchoumi"]
    writer = storage.RawJsonlWriter(category=spec.category, source=spec.name)
    writer.write(RawRecord(source=spec.name, source_listing_id="1", url="http://x"))
    writer.close()

    report = bronze.check_lot(writer.path)

    assert report.ok, report.failures
    assert all(check.name != "métadonnées" for check in report.checks)


def test_check_lot_reports_failure(monkeypatch, tmp_path) -> None:
    """Un lot invalide est signalé : le statut consigné ne ment pas."""
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    writer = storage.RawJsonlWriter(category=config.CATEGORY_LISTINGS, source="koutchoumi")
    writer.write(RawRecord(source="koutchoumi", source_listing_id="1", url="http://x"))
    writer.close()
    with writer.path.open("a", encoding="utf-8") as handle:
        handle.write("pas du json\n")

    report = bronze.check_lot(writer.path)

    assert not report.ok
    assert [check.name for check in report.failures] == ["format JSON"]


def test_check_lot_can_require_metadata(monkeypatch, tmp_path) -> None:
    """Métadonnées exigées : leur absence est un échec explicite."""
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    writer = storage.RawJsonlWriter(category=config.CATEGORY_LISTINGS, source="koutchoumi")
    writer.write(RawRecord(source="koutchoumi", source_listing_id="1", url="http://x"))
    writer.close()

    report = bronze.check_lot(writer.path, expect_metadata=True)

    assert any(check.name == "métadonnées" and not check.ok for check in report.checks)


def test_cli_records_lot_validation_status(monkeypatch, tmp_path) -> None:
    """Le CLI de collecte consigne le statut de validation dans les métadonnées."""
    data_root = tmp_path / "data"
    samples = data_root / "samples"
    samples.mkdir(parents=True)
    with (samples / "tiny.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["price", "city"])
        writer.writeheader()
        writer.writerow({"price": "120000", "city": "Douala"})

    monkeypatch.setattr(config, "DATA_ROOT", data_root)
    monkeypatch.setattr(config, "RAW_ROOT", data_root / "raw")
    monkeypatch.setattr(config, "SAMPLES_ROOT", samples)

    exit_code = ingestion_cli.main(["--source", "reference_local"])

    assert exit_code == 0
    metadata_files = list((data_root / "raw" / "metadata").glob("*/*.json"))
    assert len(metadata_files) == 1
    payload = json.loads(metadata_files[0].read_text(encoding="utf-8"))
    assert payload["lot_validation_status"] == "ok"
    assert payload["record_count"] == 1
    assert payload["content_sha256"]
