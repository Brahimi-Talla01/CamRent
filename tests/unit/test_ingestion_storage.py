"""Tests du layout de stockage brut et des métadonnées de lot."""

from __future__ import annotations

import hashlib
import json

from ingestion import config, storage
from ingestion.models import RawRecord


def test_writer_uses_spec_layout(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")

    writer = storage.RawJsonlWriter(category=config.CATEGORY_LISTINGS, source="koutchoumi")
    writer.write(RawRecord(source="koutchoumi", source_listing_id="1", url="http://x"))
    writer.close()

    rel = writer.path.relative_to(config.RAW_ROOT)
    assert rel.parts[0] == "listings"

    lines = writer.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["source"] == "koutchoumi"


def test_second_run_does_not_overwrite(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")

    first = storage.RawJsonlWriter(
        category=config.CATEGORY_LISTINGS, source="koutchoumi", stamp="010101"
    )
    first.write(RawRecord(source="koutchoumi", source_listing_id="1", url="http://x"))
    first.close()

    second = storage.RawJsonlWriter(
        category=config.CATEGORY_LISTINGS, source="koutchoumi", stamp="020202"
    )
    second.write(RawRecord(source="koutchoumi", source_listing_id="2", url="http://y"))
    second.close()

    assert first.path != second.path
    assert first.path.exists()
    assert second.path.exists()


def test_empty_writer_leaves_no_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")

    writer = storage.RawJsonlWriter(category=config.CATEGORY_REFERENCE, source="geloka")
    writer.abort()

    assert not writer.path.exists()


def test_metadata_records_count_and_category(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    spec = config.SOURCES["koutchoumi"]

    writer = storage.RawJsonlWriter(category=spec.category, source=spec.name)
    writer.write(RawRecord(source=spec.name, source_listing_id="1", url="http://x"))
    writer.close()

    meta_path = storage.write_metadata(spec, writer, list(spec.urls))
    payload = json.loads(meta_path.read_text(encoding="utf-8"))

    assert payload["record_count"] == 1
    assert payload["category"] == "listings"
    assert payload["rights_status"] == spec.rights
    assert payload["raw_file"] == str(writer.path.relative_to(config.RAW_ROOT))


def test_metadata_records_provenance(monkeypatch, tmp_path) -> None:
    """Provenance consignée : version du connecteur et empreinte du contenu."""
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    spec = config.SOURCES["koutchoumi"]

    writer = storage.RawJsonlWriter(category=spec.category, source=spec.name)
    writer.write(RawRecord(source=spec.name, source_listing_id="1", url="http://x"))
    writer.close()

    meta_path = storage.write_metadata(spec, writer, list(spec.urls))
    payload = json.loads(meta_path.read_text(encoding="utf-8"))

    assert payload["connector_version"] == config.CONNECTOR_VERSION
    assert payload["content_bytes"] == writer.path.stat().st_size
    assert payload["content_sha256"] == hashlib.sha256(
        writer.path.read_bytes()
    ).hexdigest()
    assert payload["lot_validation_status"] == "not_run"
    assert payload["lot_validation_failures"] == []


def test_content_digest_changes_with_content(monkeypatch, tmp_path) -> None:
    """L'empreinte distingue deux lots dont le contenu diffère."""
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")

    first = storage.RawJsonlWriter(
        category=config.CATEGORY_LISTINGS, source="koutchoumi", stamp="010101"
    )
    first.write(RawRecord(source="koutchoumi", source_listing_id="1", url="http://x"))
    first.close()

    second = storage.RawJsonlWriter(
        category=config.CATEGORY_LISTINGS, source="koutchoumi", stamp="020202"
    )
    second.write(RawRecord(source="koutchoumi", source_listing_id="2", url="http://y"))
    second.close()

    first_digest, first_size = storage.content_digest(first.path)
    second_digest, second_size = storage.content_digest(second.path)

    assert first_digest != second_digest
    assert first_digest == hashlib.sha256(first.path.read_bytes()).hexdigest()
    assert first_size == first.path.stat().st_size
    assert second_size == second.path.stat().st_size


def test_metadata_records_validation_status(monkeypatch, tmp_path) -> None:
    """Le statut de validation du lot est consigné tel que fourni."""
    monkeypatch.setattr(config, "RAW_ROOT", tmp_path / "raw")
    spec = config.SOURCES["koutchoumi"]

    writer = storage.RawJsonlWriter(category=spec.category, source=spec.name)
    writer.write(RawRecord(source=spec.name, source_listing_id="1", url="http://x"))
    writer.close()

    meta_path = storage.write_metadata(
        spec,
        writer,
        list(spec.urls),
        validation_status="failed",
        validation_failures=["format JSON"],
    )
    payload = json.loads(meta_path.read_text(encoding="utf-8"))

    assert payload["lot_validation_status"] == "failed"
    assert payload["lot_validation_failures"] == ["format JSON"]
