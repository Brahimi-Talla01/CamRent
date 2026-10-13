"""Tests des baselines (Phase 5) : valeurs apprises, replis et garde-fous."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.src import baselines


def test_global_baseline_predicts_the_train_mean(ml_frame: pd.DataFrame) -> None:
    baseline = baselines.GlobalMeanBaseline().fit(ml_frame)
    expected = round(float(ml_frame["target_rent_price"].mean()))
    assert np.allclose(baseline.predict(ml_frame), expected)
    assert baseline.describe()["valeur_apprise"] == expected


def test_city_baseline_uses_city_medians(ml_frame: pd.DataFrame) -> None:
    baseline = baselines.GroupMedianBaseline(("city",), name="baseline_city")
    baseline.fit(ml_frame)
    values = baseline.predict(ml_frame)
    by_city = dict(zip(ml_frame["city"], values, strict=True))
    assert by_city["Douala"] == 200_000
    assert by_city["Yaoundé"] == 500_000
    assert baseline.describe()["groupes"] == 2


def test_city_baseline_falls_back_to_global_mean_for_unseen_city(
    ml_frame: pd.DataFrame,
) -> None:
    global_baseline = baselines.GlobalMeanBaseline()
    baseline = baselines.GroupMedianBaseline(
        ("city",), name="baseline_city", fallback=global_baseline
    ).fit(ml_frame)
    unseen = pd.DataFrame(
        {
            "city": ["Kribi"],
            "neighborhood": ["Centre"],
            "property_type": ["apartment"],
            "target_rent_price": [0],
        }
    )
    values, levels = baseline.predict_with_levels(unseen)
    assert values[0] == pytest.approx(float(ml_frame["target_rent_price"].mean()))
    assert levels[0] == "baseline_global"


def test_neighborhood_baseline_uses_group_then_fallback_chain(
    ml_frame: pd.DataFrame,
) -> None:
    neighborhood = next(
        baseline
        for baseline in baselines.build_baselines()
        if baseline.name == "baseline_neighborhood"
    )
    neighborhood.fit(ml_frame)
    probe = pd.DataFrame(
        {
            "city": ["Douala", "Douala", "Kribi"],
            "neighborhood": ["Bali", "Bali", "Centre"],
            "property_type": ["apartment", "house", "apartment"],
        }
    )
    values, levels = neighborhood.predict_with_levels(probe)
    # groupe connu
    assert values[0] == 150_000
    assert levels[0] == "baseline_neighborhood"
    # couple (quartier, type) inconnu → repli ville + type inconnu → médiane ville
    assert values[1] == 200_000
    assert levels[1] == "baseline_city"
    # ville inconnue → moyenne globale
    assert values[2] == pytest.approx(float(ml_frame["target_rent_price"].mean()))
    assert levels[2] == "baseline_global"


def test_group_baseline_without_fallback_fails_loudly(ml_frame: pd.DataFrame) -> None:
    baseline = baselines.GroupMedianBaseline(("city",), name="baseline_city").fit(ml_frame)
    unseen = pd.DataFrame({"city": ["Kribi"], "property_type": ["apartment"]})
    with pytest.raises(RuntimeError, match="aucun repli"):
        baseline.predict(unseen)


def test_baselines_require_fit_before_predict(ml_frame: pd.DataFrame) -> None:
    with pytest.raises(RuntimeError, match="entraînée"):
        baselines.GlobalMeanBaseline().predict(ml_frame)
    with pytest.raises(RuntimeError, match="entraînée"):
        baselines.GroupMedianBaseline(("city",)).predict(ml_frame)


def test_baselines_reject_empty_training_frame(ml_frame: pd.DataFrame) -> None:
    empty = ml_frame.iloc[0:0]
    with pytest.raises(ValueError, match="dataset vide"):
        baselines.GlobalMeanBaseline().fit(empty)
    with pytest.raises(ValueError, match="dataset vide"):
        baselines.GroupMedianBaseline(("city",)).fit(empty)


def test_baselines_reject_missing_target_values(ml_frame: pd.DataFrame) -> None:
    broken = ml_frame.copy()
    broken.loc[0, "target_rent_price"] = None
    with pytest.raises(ValueError, match="valeurs manquantes"):
        baselines.GlobalMeanBaseline().fit(broken)


def test_build_baselines_exposes_the_three_spec_baselines() -> None:
    names = [baseline.name for baseline in baselines.build_baselines()]
    assert names == ["baseline_global", "baseline_city", "baseline_neighborhood"]
    described = {baseline.name: baseline.describe() for baseline in baselines.build_baselines()}
    assert described["baseline_city"]["repli"] == "baseline_global"
    assert described["baseline_neighborhood"]["repli"] == "baseline_city_type"
    assert described["baseline_neighborhood"]["cles"] == [
        "city",
        "neighborhood",
        "property_type",
    ]
