"""Tests du chargement et de la qualification du dataset ML (Phase 5)."""

from __future__ import annotations

import pandas as pd
import pytest

from ml.src import config, data


def test_validate_columns_accepts_the_mart_schema(ml_frame: pd.DataFrame) -> None:
    data.validate_columns(ml_frame)


def test_validate_columns_reports_every_missing_column(ml_frame: pd.DataFrame) -> None:
    incomplete = ml_frame.drop(columns=["city", "target_rent_price"])
    with pytest.raises(ValueError) as error:
        data.validate_columns(incomplete)
    message = str(error.value)
    assert "city" in message
    assert "target_rent_price" in message


def test_load_ml_dataset_requires_a_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        data.load_ml_dataset()


def test_load_ml_dataset_reads_the_mart_table(
    monkeypatch: pytest.MonkeyPatch, ml_frame: pd.DataFrame
) -> None:
    queries: list[str] = []

    def fake_read_sql(query: str, engine: object) -> pd.DataFrame:
        queries.append(query)
        return ml_frame

    monkeypatch.setattr(pd, "read_sql", fake_read_sql)
    frame = data.load_ml_dataset(engine=object())

    assert len(frame) == len(ml_frame)
    assert queries == [f'select * from "{config.SOURCE_SCHEMA}"."{config.SOURCE_TABLE}"']


def test_scenario_frames_keep_every_row_in_the_primary_scenario(
    ml_frame: pd.DataFrame,
) -> None:
    scenarios = data.scenario_frames(ml_frame)
    assert list(scenarios) == list(data.SCENARIOS)
    assert len(scenarios["toutes_observations"]) == 6
    assert len(scenarios["hors_republications"]) == 5  # seule l2 est une republication
    # l3 et l6 ont un prix borné ; l6 porte aussi une aberration
    assert len(scenarios["prix_exacts_sans_aberration"]) == 4


def test_scenario_frames_never_mutate_the_source(ml_frame: pd.DataFrame) -> None:
    before = ml_frame.copy(deep=True)
    data.scenario_frames(ml_frame)
    pd.testing.assert_frame_equal(ml_frame, before)


def test_describe_quality_counts_markers(ml_frame: pd.DataFrame) -> None:
    quality = data.describe_quality(ml_frame)
    assert quality["n_observations"] == 6
    assert quality["prix_borne"] == 2
    assert quality["republications"] == 1
    assert quality["aberrations"] == 1
    assert quality["quartiers_non_reconnus"] == 0
    assert quality["villes"] == ["Douala", "Yaoundé"]
    assert quality["quartiers"] == 3
    assert quality["paires_ville_quartier_type"] == 4


def test_describe_chronology_shows_no_usable_time_information(
    ml_frame: pd.DataFrame,
) -> None:
    chronology = data.describe_chronology(ml_frame)
    assert chronology["posted_at_renseignes"] == 0
    assert chronology["jours_de_collecte_distincts"] == 1
    assert chronology["collected_at_min"] is not None
