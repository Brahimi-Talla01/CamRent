"""Tests des métriques d'évaluation (Phase 5)."""

from __future__ import annotations

import numpy as np
import pytest

from ml.src import evaluation

TRUTH = [100.0, 200.0, 300.0]
PREDICTED = [110.0, 180.0, 330.0]


def test_regression_metrics_values() -> None:
    metrics = evaluation.regression_metrics(TRUTH, PREDICTED)
    assert metrics["n"] == 3
    assert metrics["mae"] == 20  # (10 + 20 + 30) / 3
    assert metrics["rmse"] == round((1400 / 3) ** 0.5)  # 22
    assert metrics["medae"] == 20
    assert metrics["erreur_absolue_p90"] == 28  # quantile linéaire de [10, 20, 30]
    assert metrics["r2"] == round(1 - 1400 / 20000, 4)  # 0.93
    assert metrics["prix_moyen_observe"] == 200


def test_r2_is_null_with_a_single_observation() -> None:
    metrics = evaluation.regression_metrics([100.0], [100.0])
    assert metrics["n"] == 1
    assert metrics["mae"] == 0
    assert metrics["r2"] is None


def test_perfect_prediction_has_zero_error() -> None:
    metrics = evaluation.regression_metrics(TRUTH, TRUTH)
    assert metrics["mae"] == 0
    assert metrics["rmse"] == 0
    assert metrics["r2"] == 1.0


def test_regression_metrics_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError, match="Tailles incohérentes"):
        evaluation.regression_metrics([1.0, 2.0], [1.0])
    with pytest.raises(ValueError, match="ensemble vide"):
        evaluation.regression_metrics([], [])
    with pytest.raises(ValueError, match="valeurs manquantes"):
        evaluation.regression_metrics([1.0, float("nan")], [1.0, 2.0])


def test_price_quartiles_are_computed_on_training_only() -> None:
    edges = evaluation.price_quartile_edges([100, 200, 300, 400])
    assert edges[1] == 175
    labels = evaluation.price_level_labels([100, 200, 300, 400], edges)
    assert labels.tolist() == ["Q1", "Q2", "Q3", "Q4"]


def test_price_quartiles_require_enough_training_rows() -> None:
    with pytest.raises(ValueError, match="Au moins 4"):
        evaluation.price_quartile_edges([1, 2, 3])


def test_bedrooms_labels_isolate_missing_values() -> None:
    labels = evaluation.bedrooms_labels([1, 2, None])
    assert labels.tolist() == ["1 chambre(s)", "2 chambre(s)", "inconnu"]


def test_segment_metrics_publish_the_observation_count() -> None:
    segments = ["Douala", "Douala", "Douala", "Yaoundé"]
    truth = [100.0, 200.0, 300.0, 1_000.0]
    predicted = [110.0, 190.0, 330.0, 900.0]
    rows = evaluation.segment_metrics(truth, predicted, segments, segment_column="ville")
    assert [row["ville"] for row in rows] == ["Douala", "Yaoundé"]
    douala = rows[0]
    assert douala["n"] == 3
    assert douala["mae"] == 17  # (10 + 10 + 30) / 3, arrondi
    yaounde = rows[1]
    assert yaounde["n"] == 1
    assert yaounde["mae"] == 100
    assert yaounde["r2"] is None


def test_segment_metrics_flag_small_segments_without_hiding_them() -> None:
    segments = ["Douala", "Douala", "Yaoundé"]
    rows = evaluation.segment_metrics(
        [100.0, 200.0, 300.0],
        [100.0, 200.0, 300.0],
        segments,
        min_n=2,
        segment_column="ville",
    )
    assert [row["ville"] for row in rows] == ["Douala", "Yaoundé"]
    assert [row["sous_seuil_de_publication"] for row in rows] == [False, True]


def test_segment_metrics_reject_misaligned_segments() -> None:
    with pytest.raises(ValueError, match="même longueur"):
        evaluation.segment_metrics([1.0, 2.0], [1.0, 2.0], ["a"], segment_column="ville")


def test_bootstrap_ci_brackets_the_mae_and_is_deterministic() -> None:
    truth = np.linspace(100_000, 500_000, 200)
    predicted = truth - 10_000
    first = evaluation.bootstrap_mae_ci(truth, predicted, iterations=200, seed=3)
    second = evaluation.bootstrap_mae_ci(truth, predicted, iterations=200, seed=3)
    assert first == second
    assert first["mae_borne_basse"] <= first["mae"] <= first["mae_borne_haute"]
    assert first["n"] == 200


def test_bootstrap_ci_rejects_invalid_iterations() -> None:
    with pytest.raises(ValueError, match="iterations"):
        evaluation.bootstrap_mae_ci(TRUTH, PREDICTED, iterations=0)
