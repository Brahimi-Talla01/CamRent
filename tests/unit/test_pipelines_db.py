"""Tests du chargeur des tables d'atterrissage PostgreSQL (Phase 4 — Data marts).

Niveau unitaire : la connexion est **simulée** ; le but est de vérifier le
comportement du chargeur (fichier manquant, URL manquante, création du schéma,
stratégie idempotente vidage+insertion et volume chargé) pour le Silver, la
quarantaine et les métadonnées de lot (lot B).
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import pytest

from pipelines import config, db


def _fake_silver_parquet(tmp_path, rows: int = 3) -> Any:
    """Écrit un mini Silver Parquet et retourne son chemin."""
    frame = pd.DataFrame(
        {
            "source": ["koutchoumi"] * rows,
            "source_file": ["koutchoumi (live)"] * rows,
            "source_listing_id": [f"k-{i}" for i in range(rows)],
            "rent_price": [100000 * (i + 1) for i in range(rows)],
            "city": ["Douala"] * rows,
            "neighborhood": ["Bonapriso"] * rows,
            "property_type": ["studio"] * rows,
        }
    )
    path = tmp_path / config.SILVER_FILENAME
    # Moteur par défaut : pyarrow en CI, fastparquet en local — le test suit
    # ainsi l'environnement comme le fait `pipelines/db.py`.
    frame.to_parquet(path, index=False)
    return path


class _FakeEngine:
    """Mimique un Engine SQLAlchemy minimal pour vérifier les appels."""

    def __init__(self) -> None:
        self.executed: list[str] = []

    def begin(self) -> Any:
        return _FakeCtx(self)

    def dispose(self) -> None:
        self.executed.append("dispose")


class _FakeCtx:
    def __init__(self, engine: _FakeEngine) -> None:
        self._engine = engine

    def exec_driver_sql(self, statement: str) -> None:
        self._engine.executed.append(statement)

    def __enter__(self) -> _FakeCtx:
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _FakeInspector:
    def __init__(self, has_table: bool) -> None:
        self._has_table = has_table

    def has_table(self, table: str, schema: str | None = None) -> bool:
        return self._has_table


def test_load_requires_silver_file(monkeypatch) -> None:
    """Erreur claire si le Parquet Silver n'existe pas."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake:fake@localhost:5432/fake")
    with pytest.raises(FileNotFoundError, match="python -m pipelines silver"):
        db.load_silver_to_postgres(silver_path=config.PROCESSED_ROOT / "inexistant.parquet")


def test_load_requires_database_url(monkeypatch, tmp_path) -> None:
    """Erreur claire si DATABASE_URL est absent (avant toute lecture Parquet)."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    path = _fake_silver_parquet(tmp_path)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        db.load_silver_to_postgres(silver_path=path)


def _patch_engine(monkeypatch, table_exists: bool) -> tuple[_FakeEngine, dict[str, Any]]:
    """Branche un faux Engine + faux inspecteur et capture les appels to_sql."""
    engine = _FakeEngine()
    captured: dict[str, Any] = {}

    def fake_create_engine(url: str, **kwargs: Any) -> _FakeEngine:
        captured["url"] = url
        return engine

    def fake_inspect(engine_arg: Any) -> _FakeInspector:
        return _FakeInspector(table_exists)

    def fake_to_sql(frame: pd.DataFrame, table: str, engine_arg: Any, **kwargs: Any) -> None:
        captured["table"] = table
        captured["schema"] = kwargs.get("schema")
        captured["if_exists"] = kwargs.get("if_exists")
        captured["rows"] = len(frame)

    monkeypatch.setattr("sqlalchemy.create_engine", fake_create_engine)
    monkeypatch.setattr("sqlalchemy.inspect", fake_inspect)
    monkeypatch.setattr(pd.DataFrame, "to_sql", fake_to_sql)
    return engine, captured


def test_load_creates_schema_and_disposes(monkeypatch, tmp_path) -> None:
    """Table absente : le schéma `landing` est créé, données insérées, engine disposé."""
    path = _fake_silver_parquet(tmp_path, rows=5)
    engine, captured = _patch_engine(monkeypatch, table_exists=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://camrent:change-me@localhost:5433/camrent")

    result = db.load_silver_to_postgres(silver_path=path)

    assert 'CREATE SCHEMA IF NOT EXISTS "landing"' in engine.executed[0]
    assert "dispose" in engine.executed
    assert "TRUNCATE" not in " ".join(engine.executed)
    assert captured["table"] == db.LANDING_TABLE
    assert captured["schema"] == db.LANDING_SCHEMA
    assert captured["if_exists"] == "fail"
    assert captured["rows"] == 5
    assert result["rows"] == 5
    assert result["table"] == "landing.silver_listings"


def test_load_replays_without_dropping_table(monkeypatch, tmp_path) -> None:
    """Table existante : vidée par TRUNCATE puis réinsérée (jamais DROP)."""
    path = _fake_silver_parquet(tmp_path, rows=4)
    engine, captured = _patch_engine(monkeypatch, table_exists=True)
    monkeypatch.setenv("DATABASE_URL", "postgresql://camrent:change-me@localhost:5433/camrent")

    db.load_silver_to_postgres(silver_path=path)

    statements = " ".join(engine.executed)
    assert 'TRUNCATE TABLE "landing"."silver_listings"' in statements
    assert all("DROP" not in s for s in engine.executed)
    assert captured["if_exists"] == "append"
    assert captured["rows"] == 4


def test_landing_table_name_is_canonical() -> None:
    """La table d'atterrissage suit la convention (schéma landing)."""
    assert db.LANDING_TABLE == "silver_listings"


def _fake_quarantine_parquet(tmp_path, rows: int = 2) -> Any:
    """Écrit un mini Parquet de quarantaine et retourne son chemin."""
    frame = pd.DataFrame(
        {
            "source": ["koutchoumi"] * rows,
            "source_file": ["koutchoumi (live)"] * rows,
            "source_listing_id": [f"q-{i}" for i in range(rows)],
            "quarantine_reason": ["prix_manquant"] * (rows - 1) + ["type_inconnu"],
        }
    )
    path = tmp_path / config.QUARANTINE_FILENAME
    frame.to_parquet(path, index=False)
    return path


def test_quarantine_load_is_idempotent(monkeypatch, tmp_path) -> None:
    """La quarantaine est chargée dans son propre table et jamais droppée."""
    path = _fake_quarantine_parquet(tmp_path, rows=3)
    engine, captured = _patch_engine(monkeypatch, table_exists=True)
    monkeypatch.setenv("DATABASE_URL", "postgresql://camrent:change-me@localhost:5433/camrent")

    result = db.load_quarantine_to_postgres(quarantine_path=path)

    assert captured["table"] == db.QUARANTINE_TABLE
    assert captured["if_exists"] == "append"
    assert captured["rows"] == 3
    assert result["table"] == "landing.quarantine_listings"
    assert result["by_reason"] == {"prix_manquant": 2, "type_inconnu": 1}
    statements = " ".join(engine.executed)
    assert 'TRUNCATE TABLE "landing"."quarantine_listings"' in statements
    assert all("DROP" not in statement for statement in engine.executed)


def test_read_ingestion_runs_exposes_provenance(monkeypatch, tmp_path) -> None:
    """Un lot récent expose version de connecteur, empreinte et statut."""
    meta_dir = tmp_path / "metadata" / "2026-10-16"
    meta_dir.mkdir(parents=True)
    (meta_dir / "koutchoumi_070000.json").write_text(
        json.dumps(
            {
                "source": "koutchoumi",
                "category": "listings",
                "method": "http_get_html_parse",
                "format": "jsonl",
                "collected_at": "2026-10-16T07:00:00+00:00",
                "collected_day": "2026-10-16",
                "record_count": 12,
                "raw_file": "listings/2026-10-16/koutchoumi_070000.jsonl",
                "urls": ["https://example.test/a"],
                "rights_status": "uncertain",
                "connector_version": "0.1.0",
                "content_bytes": 4096,
                "content_sha256": "a" * 64,
                "lot_validation_status": "ok",
                "lot_validation_failures": [],
            }
        ),
        encoding="utf-8",
    )

    rows = db.read_ingestion_runs(tmp_path)

    assert len(rows) == 1
    assert rows[0]["connector_version"] == "0.1.0"
    assert rows[0]["content_sha256"] == "a" * 64
    assert rows[0]["lot_validation_status"] == "ok"
    assert rows[0]["record_count"] == 12
    assert rows[0]["n_urls"] == 1


def test_read_ingestion_runs_keeps_unreadable_lot(tmp_path) -> None:
    """Un lot illisible est conservé et signalé, jamais écarté en silence."""
    meta_dir = tmp_path / "metadata" / "2026-10-09"
    meta_dir.mkdir(parents=True)
    (meta_dir / "geloka_070536.json").write_text("{pas du json", encoding="utf-8")

    rows = db.read_ingestion_runs(tmp_path)

    assert len(rows) == 1
    assert rows[0]["lot_validation_status"] == "unreadable"
    assert rows[0]["raw_file"] == "metadata/2026-10-09/geloka_070536.json"


def test_read_ingestion_runs_keeps_null_provenance_for_old_lots(tmp_path) -> None:
    """Les lots antérieurs n'ont pas de provenance : aucune valeur inventée."""
    meta_dir = tmp_path / "metadata" / "2026-10-09"
    meta_dir.mkdir(parents=True)
    (meta_dir / "geloka_070536.json").write_text(
        json.dumps(
            {
                "source": "geloka",
                "record_count": 8,
                "urls": [],
                "raw_file": "reference_data/2026-10-09/geloka_070536.jsonl",
            }
        ),
        encoding="utf-8",
    )

    rows = db.read_ingestion_runs(tmp_path)

    assert rows[0]["connector_version"] is None
    assert rows[0]["content_sha256"] is None
    assert rows[0]["lot_validation_status"] is None


def test_load_ingestion_runs_loads_one_row_per_lot(monkeypatch, tmp_path) -> None:
    """Les lots sont chargés dans `landing.ingestion_runs` (une ligne par lot)."""
    meta_dir = tmp_path / "metadata" / "2026-10-09"
    meta_dir.mkdir(parents=True)
    for name, source in (
        ("geloka_070536", "geloka"),
        ("reference_local_070536", "reference_local"),
    ):
        (meta_dir / f"{name}.json").write_text(
            json.dumps({"source": source, "record_count": 3}),
            encoding="utf-8",
        )
    engine, captured = _patch_engine(monkeypatch, table_exists=True)
    monkeypatch.setenv("DATABASE_URL", "postgresql://camrent:change-me@localhost:5433/camrent")

    result = db.load_ingestion_runs_to_postgres(raw_root=tmp_path)

    assert captured["table"] == db.INGESTION_RUNS_TABLE
    assert captured["rows"] == 2
    assert result["rows"] == 2
    assert result["sources"] == ["geloka", "reference_local"]
    assert result["table"] == "landing.ingestion_runs"


def test_load_all_requires_quarantine_file(monkeypatch, tmp_path) -> None:
    """Une quarantaine absente échoue clairement (pas de chargement partiel silencieux)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake:fake@localhost:5432/fake")
    with pytest.raises(FileNotFoundError, match="pipelines silver"):
        db.load_quarantine_to_postgres(
            quarantine_path=config.PROCESSED_ROOT / "inexistant.parquet"
        )


def test_load_all_loads_the_three_tables(monkeypatch, tmp_path) -> None:
    """`load_all_to_postgres` charge Silver, quarantaine et lots."""
    silver = _fake_silver_parquet(tmp_path, rows=5)
    quarantine = _fake_quarantine_parquet(tmp_path, rows=2)
    meta_dir = tmp_path / "raw" / "metadata" / "2026-10-16"
    meta_dir.mkdir(parents=True)
    (meta_dir / "koutchoumi_070000.json").write_text(
        json.dumps({"source": "koutchoumi", "record_count": 5}), encoding="utf-8"
    )
    _patch_engine(monkeypatch, table_exists=True)
    monkeypatch.setenv("DATABASE_URL", "postgresql://camrent:change-me@localhost:5433/camrent")

    result = db.load_all_to_postgres(
        silver_path=silver,
        quarantine_path=quarantine,
        raw_root=tmp_path / "raw",
    )

    assert set(result) == {"silver", "quarantine", "ingestion_runs"}
    assert result["silver"]["rows"] == 5
    assert result["quarantine"]["rows"] == 2
    assert result["ingestion_runs"]["rows"] == 1
