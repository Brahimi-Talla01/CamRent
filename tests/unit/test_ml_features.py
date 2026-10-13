"""Tests de la construction des features (Phase 6)."""

from __future__ import annotations

import pandas as pd
import pytest

from ml.src import features


def test_feature_builder_adds_derived_features(ml_frame: pd.DataFrame) -> None:
    built = features.FeatureBuilder().fit_transform(ml_frame)
    assert list(built.columns) == list(features.MODEL_FEATURES)
    assert built["total_pieces"].tolist() == [4, 5, 2, 4, 3, 6]


def test_market_depth_counts_come_from_training_only(ml_frame: pd.DataFrame) -> None:
    builder = features.FeatureBuilder().fit(ml_frame)
    unseen = pd.DataFrame(
        {
            "city": ["Douala", "Kribi"],
            "neighborhood": ["Bali", "Centre"],
            "property_type": ["apartment", "apartment"],
            "bedrooms": [2, 2],
            "bathrooms": [1, 1],
        }
    )
    built = builder.transform(unseen)
    # Bali apparaît 3 fois à l'entraînement, Kribi/Centre est inconnu → 0
    assert built["logements_dans_quartier"].tolist() == [3.0, 0.0]


def test_market_depth_encoder_requires_fit() -> None:
    with pytest.raises(RuntimeError, match="ajusté"):
        features.MarketDepthEncoder().transform(pd.DataFrame({"city": ["Douala"]}))


def test_feature_builder_encodes_missing_values_without_imputation(
    ml_frame: pd.DataFrame,
) -> None:
    frame = ml_frame.copy()
    frame["bedrooms"] = frame["bedrooms"].astype("float")
    frame.loc[0, "bedrooms"] = None
    built = features.FeatureBuilder().fit_transform(frame)
    assert built["bedrooms"].isna().tolist()[0] is True
    # les autres lignes restent intactes (aucune imputation à ce stade)
    assert built["bedrooms"].notna().sum() == 5


def test_model_features_exclude_the_target_and_flags() -> None:
    assert "target_rent_price" not in features.MODEL_FEATURES
    assert "rent_per_m2" in features.EXCLUDED_FEATURES
    assert "price_is_bound" in features.EXCLUDED_FEATURES
    assert set(features.MODEL_FEATURES) == set(
        features.CATEGORICAL_FEATURES + features.NUMERIC_FEATURES + features.DERIVED_FEATURES
    )
