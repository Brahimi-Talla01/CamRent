"""Tests des intervalles de prédiction (Phase 6).

Ce qui est vérifié ici, c'est la **validité statistique** de la fourchette :
couverture empirique mesurée, calibration faite sur la validation seulement,
et aucune fourchette impossible (borne basse < 0).
"""

from __future__ import annotations

import numpy as np
import pytest

from ml.src import config, uncertainty


def test_conformal_width_is_the_validation_quantile() -> None:
    truth = [100.0, 200.0, 300.0, 400.0, 500.0]
    predicted = [110.0, 180.0, 330.0, 380.0, 500.0]
    interval = uncertainty.ConformalInterval(alpha=0.2).fit(truth, predicted)
    residuals = np.abs(np.array(truth) - np.array(predicted))
    assert interval.demi_largeur == pytest.approx(float(np.quantile(residuals, 0.8)))


def test_conformal_bounds_are_symmetric_and_non_negative() -> None:
    # demi-largeur de calibration = 20 FCFA
    interval = uncertainty.ConformalInterval(alpha=0.1).fit([100.0], [120.0])
    low, high = interval.bounds([5.0, 1_000.0])
    assert low[0] == uncertainty.MIN_RENT  # 5 - 20 < 0 → plancher à 1 FCFA
    assert high[0] == 25.0
    assert low[1] == 980.0
    assert high[1] == 1_020.0
    assert np.all(high >= low)


def test_conformal_requires_calibration() -> None:
    with pytest.raises(RuntimeError, match="non calibré"):
        uncertainty.ConformalInterval().bounds([100.0])
    with pytest.raises(ValueError, match="sans résidus"):
        uncertainty.ConformalInterval().fit([], [])


def test_coverage_report_measures_the_nominal_level() -> None:
    truth = np.arange(100, 200, dtype=float)
    lower = truth - 5
    upper = truth + 5
    report = uncertainty.coverage_report(truth, lower, upper)
    assert report["n"] == 100
    assert report["couverture_pct"] == 100.0
    assert report["largeur_moyenne"] == 10
    assert report["largeur_mediane"] == 10


def test_coverage_report_keeps_missing_points_visible() -> None:
    truth = [0.0, 100.0, 1_000.0]
    report = uncertainty.coverage_report(truth, [0.0, 0.0, 0.0], [1.0, 1.0, 1.0])
    assert report["couverture_pct"] == round(100 / 3, 2)


@pytest.mark.parametrize(
    ("truth", "lower", "upper", "message"),
    [
        ([1.0], [1.0, 2.0], [3.0], "tailles incohérentes"),
        ([], [], [], "ensemble vide"),
        ([1.0], [3.0], [2.0], "borne haute inférieure"),
    ],
)
def test_coverage_report_rejects_invalid_inputs(
    truth: list[float], lower: list[float], upper: list[float], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        uncertainty.coverage_report(truth, lower, upper)


def test_choose_method_prefers_the_narrowest_covering_method() -> None:
    results = {
        "split_conformal": {"validation": {"couverture_pct": 89.0, "largeur_mediane": 400_000}},
        "quantile_regression": {
            "validation": {"couverture_pct": 92.0, "largeur_mediane": 300_000}
        },
    }
    retained, rationale = uncertainty.choose_method(results, alpha=0.1)
    assert retained == "quantile_regression"
    assert "90 %" in rationale


def test_choose_method_falls_back_to_the_closest_coverage() -> None:
    results = {
        "split_conformal": {"validation": {"couverture_pct": 70.0, "largeur_mediane": 10.0}},
        "quantile_regression": {
            "validation": {"couverture_pct": 80.0, "largeur_mediane": 20.0}
        },
    }
    retained, rationale = uncertainty.choose_method(results, alpha=0.1)
    assert retained == "quantile_regression"
    assert "Aucune méthode" in rationale


def test_quantile_regression_interval_is_ordered_and_clamped(ml_dataset) -> None:
    inputs = ml_dataset[list(config.FEATURE_COLUMNS)]
    truth = ml_dataset[config.TARGET]
    interval = uncertainty.QuantileRegressionInterval(alpha=0.2, seed=5).fit(inputs, truth)
    low, high = interval.bounds(inputs)
    assert np.all(low <= high)
    assert np.all(low >= uncertainty.MIN_RENT)
    assert interval.describe()["quantiles"] == pytest.approx([0.1, 0.9])
    with pytest.raises(RuntimeError, match="non entraîné"):
        uncertainty.QuantileRegressionInterval(alpha=0.2).bounds(inputs)


def test_compare_methods_reports_both_and_validates_on_test(ml_dataset) -> None:
    from ml.src import models, split, training

    parts = split.split_dataset(ml_dataset, seed=11)
    spec = next(
        item
        for item in models.build_models(11, include_lightgbm=False)
        if item.slug == "linear_brut"
    )
    estimator = spec.estimator.fit(
        parts["train"][training.features_columns()], parts["train"][config.TARGET]
    )
    predictions = {
        name: np.asarray(
            estimator.predict(parts[name][training.features_columns()]), dtype=float
        )
        for name in ("train", "validation", "test")
    }

    comparison = uncertainty.compare_methods(
        parts, predictions=predictions, alpha=0.2, seed=11
    )
    assert comparison["niveau_vise_pct"] == 80
    assert set(comparison["methodes"]) == {
        "split_conformal",
        "quantile_regression",
    }
    for block in comparison["methodes"].values():
        for name in ("validation", "test"):
            assert {"couverture_pct", "largeur_moyenne", "largeur_mediane", "n"} <= set(
                block[name]
            )
            assert 0 <= block[name]["couverture_pct"] <= 100
    retained = comparison["methode_retenue"]
    assert retained in comparison["methodes"]
    assert comparison["justification"]
    assert comparison["methodes"][retained]["validation"]["n"] == len(parts["validation"])


def test_retained_interval_rebuilds_the_selected_method(ml_dataset) -> None:
    from ml.src import split

    parts = split.split_dataset(ml_dataset, seed=11)
    predictions = {"validation": parts["validation"][config.TARGET].to_numpy(dtype=float)}
    interval = uncertainty.retained_interval(
        uncertainty.ConformalInterval.method, parts, predictions=predictions, alpha=0.2
    )
    assert interval.describe()["alpha"] == 0.2
    with pytest.raises(ValueError, match="inconnue"):
        uncertainty.retained_interval("magie", parts, predictions=predictions)
