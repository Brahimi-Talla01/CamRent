"""Tests du chargeur Silver → PostgreSQL (Phase 4 — Data marts).

Niveau unitaire : la connexion est **simulée** ; le but est de vérifier le
comportement du chargeur (fichier manquant, URL manquante, création du schéma,
stratégie idempotente vidage+insertion et volume chargé).
"""

from __future__ import annotations

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
