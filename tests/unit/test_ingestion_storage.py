"""Tests du layout de stockage brut et des métadonnées de lot."""

from __future__ import annotations

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
