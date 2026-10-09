"""Tests de la porte légale et du collecteur de référence locale."""

from __future__ import annotations

import pytest

from ingestion import config
from ingestion.http_client import LegalGateError
from ingestion.sources import COLLECTORS
from ingestion.sources.geloka import GelokaCollector
from ingestion.sources.koutchoumi import KoutchoumiCollector
from ingestion.sources.reference_local import ReferenceLocalCollector


def test_registry_covers_every_source() -> None:
    assert set(COLLECTORS) == set(config.SOURCES)


def test_uncertain_sources_require_confirm() -> None:
    with pytest.raises(LegalGateError):
        KoutchoumiCollector(config.SOURCES["koutchoumi"])
    with pytest.raises(LegalGateError):
        GelokaCollector(config.SOURCES["geloka"])


def test_confirm_legal_unlocks_collector() -> None:
    collector = KoutchoumiCollector(config.SOURCES["koutchoumi"], confirm_legal="ok")
    assert collector.NAME == "koutchoumi"


def test_local_source_has_no_gate() -> None:
    collector = ReferenceLocalCollector(config.SOURCES["reference_local"])
    assert collector.spec.requires_confirm is False


def test_reference_local_reads_csv(monkeypatch, tmp_path) -> None:
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "sample.csv").write_text(
        "Area,Bedrooms,Price\n80,2,150000\n", encoding="utf-8"
    )
    monkeypatch.setattr(config, "SAMPLES_ROOT", samples)

    collector = ReferenceLocalCollector(config.SOURCES["reference_local"])
    records = list(collector.collect())

    assert len(records) == 1
    assert records[0].source == "reference_local"
    assert records[0].source_listing_id == "sample-000000"
    assert records[0].fields["Price"] == "150000"
