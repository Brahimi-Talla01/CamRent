"""Tests du jeu synthétique de la CI (lot C — CI de données).

Le jeu est la **seule** donnée que la CI verra : s'il ne respecte pas les
contrats de la Phase 4, `dbt build` échoue en CI sans que la cause soit
évidente. Ces tests verrouillent donc le contrat côté Python (colonnes, bornes,
valeurs acceptées, unicité, déterminisme, refus d'écraser `data/` réel).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from pipelines import config
from tests.data import make_synthetic_dataset as gen

CITIES = {"Douala", "Yaoundé"}


def _listing_keys(frame: pd.DataFrame) -> pd.Series:
    source = frame["source_file"].fillna("").astype(str)
    identifiers = frame["source_listing_id"].fillna("").astype(str)
    return (source + "|" + identifiers).map(
        lambda value: hashlib.md5(value.encode("utf-8")).hexdigest()
    )


def test_silver_matches_the_project_contract() -> None:
    """Colonnes, types et bornes : le jeu passe les tests dbt du staging."""
    frame = gen.build_silver(360, gen.DEFAULT_SEED)

    assert list(frame.columns) == list(config.SILVER_COLUMNS)
    assert frame["city"].dropna().isin(CITIES).all()
    assert frame["property_type"].dropna().isin(set(gen.PROPERTY_TYPES)).all()
    assert frame["source"].isin(set(gen.SOURCES)).all()
    assert frame["rent_price"].notna().all()
    assert (frame["rent_price"] >= 1).all()
    assert frame["bedrooms"].between(0, 10).all()
    assert frame["bathrooms"].ge(0).all()
    # `listing_key` = md5(source_file | source_listing_id) doit être unique.
    assert _listing_keys(frame).is_unique


def test_implausible_rooms_are_signalled_and_kept() -> None:
    """Une valeur hors borne est conservée ET signalée (jamais supprimée)."""
    frame = gen.build_silver(360, gen.DEFAULT_SEED)
    hors_borne = frame[frame["bathrooms"] > gen.ROOMS_PLAUSIBLE_MAX]

    assert len(hors_borne) == 1
    assert "bathrooms_outlier" in str(hors_borne["outlier_flags"].iloc[0])
    # Les valeurs bornées restent dans le jeu : aucune exclusion silencieuse.
    assert len(frame) == 360


def test_quarantine_covers_every_rejection_reason() -> None:
    """Les quatre motifs existent et chaque rejet correspond à son motif."""
    frame = gen.build_quarantine(48, gen.DEFAULT_SEED)

    assert set(frame["quarantine_reason"]) == set(gen.QUARANTINE_REASONS)
    assert frame["source"].notna().all()
    assert frame["source_listing_id"].notna().all()
    assert frame.loc[
        frame["quarantine_reason"] == "prix_manquant", "rent_price"
    ].isna().all()
    assert frame.loc[frame["quarantine_reason"] == "prix_invalide", "rent_price"].eq(0).all()
    assert frame.loc[frame["quarantine_reason"] == "city_inconnue", "city"].isna().all()


def test_generate_writes_the_three_loader_inputs(tmp_path) -> None:
    """Les trois entrées de `pipelines load` sont produites et lisibles."""
    root = Path(str(tmp_path)) / "ci"
    result = gen.generate(root, silver_rows=120, quarantine_rows=16, seed=gen.DEFAULT_SEED)

    silver = pd.read_parquet(root / "processed" / config.SILVER_FILENAME)
    quarantine = pd.read_parquet(root / "processed" / config.QUARANTINE_FILENAME)
    metadata = sorted((root / "raw" / "metadata").glob("*/*.json"))

    assert result["silver_rows"] == 120
    assert len(silver) == 120
    assert len(quarantine) == 16
    assert len(metadata) == 3

    # Liseur réel du chargeur : les lots doivent être exploitables tels quels.
    from pipelines import db  # noqa: PLC0415

    lots = db.read_ingestion_runs(root / "raw")
    assert len(lots) == 3
    assert {lot["record_count"] for lot in lots} == {40, 1}
    assert any(lot["connector_version"] is None for lot in lots)  # lot sans provenance
    assert any(lot["lot_validation_status"] == "failed" for lot in lots)


def test_generation_is_deterministic(tmp_path) -> None:
    """Même graine ⇒ même contenu (reproductibilité, AGENTS.md §5)."""
    first = Path(str(tmp_path)) / "a"
    second = Path(str(tmp_path)) / "b"
    gen.generate(first, silver_rows=80, quarantine_rows=12, seed=gen.DEFAULT_SEED)
    gen.generate(second, silver_rows=80, quarantine_rows=12, seed=gen.DEFAULT_SEED)

    for relative in (
        Path("processed") / config.SILVER_FILENAME,
        Path("processed") / config.QUARANTINE_FILENAME,
    ):
        left = (first / relative).read_bytes()
        right = (second / relative).read_bytes()
        assert hashlib.sha256(left).digest() == hashlib.sha256(right).digest()

    assert sorted(p.name for p in (first / "raw" / "metadata").glob("*/*.json")) == sorted(
        p.name for p in (second / "raw" / "metadata").glob("*/*.json")
    )


def test_it_refuses_to_overwrite_the_real_data() -> None:
    """Le jeu synthétique ne peut jamais écraser `data/` du projet."""
    project_data = Path(__file__).resolve().parents[2] / "data"
    with pytest.raises(SystemExit, match="Refus d'écrire dans"):
        gen._assert_not_project_data_root(project_data)
