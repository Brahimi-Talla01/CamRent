"""Tests du zoo de modèles et des pipelines (Phase 6)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.src import config, features, models, training


def test_zoo_follows_the_spec_order_and_doubles_each_family() -> None:
    specs = models.build_models(7)
    keys = [spec.key for spec in specs]
    assert keys[:6] == ["linear", "linear", "ridge", "ridge", "lasso", "lasso"]
    assert [spec.target_transform for spec in specs[:4]] == [
        "brut",
        "log1p",
        "brut",
        "log1p",
    ]
    assert "lightgbm" in keys
    assert len(specs) == 12


def test_zoo_can_skip_the_optional_dependency() -> None:
    specs = models.build_models(7, include_lightgbm=False)
    assert len(specs) == 10
    assert all(spec.key != "lightgbm" for spec in specs)


def test_unknown_target_transform_is_rejected() -> None:
    with pytest.raises(ValueError, match="Transformation de cible inconnue"):
        models.build_pipeline(models.LinearRegression(), target_transform="log10")


def test_spec_lookup_raises_for_unknown_slug() -> None:
    with pytest.raises(KeyError, match="inconnu"):
        models.spec_by_slug(models.build_models(1), "modele_imaginaire")


@pytest.mark.parametrize("transform", list(models.TARGET_TRANSFORMS))
def test_predictions_are_in_fcfa_not_in_thousands(
    ml_frame: pd.DataFrame, transform: str
) -> None:
    """La cible brute est apprise en milliers de FCFA : la sortie doit repasser en FCFA."""
    spec = models.spec_by_slug(models.build_models(3), f"ridge_{transform}")
    estimator = spec.estimator
    columns = training.features_columns()
    estimator.fit(ml_frame[columns], ml_frame[config.TARGET])
    predictions = np.asarray(estimator.predict(ml_frame[columns]), dtype=float)

    truth = ml_frame[config.TARGET].to_numpy(dtype=float)
    assert np.all(np.isfinite(predictions))
    # une erreur d'échelle (FCFA → milliers) donnerait des prévisions ~1000x trop petites
    assert predictions.min() > truth.min() / 10
    assert predictions.max() < truth.max() * 10


@pytest.mark.parametrize(
    "key", ["linear", "ridge", "lasso", "random_forest", "gradient_boosting", "lightgbm"]
)
def test_every_family_trains_and_predicts(ml_dataset: pd.DataFrame, key: str) -> None:
    spec = models.spec_by_slug(models.build_models(5), f"{key}_brut")
    columns = training.features_columns()
    estimator = spec.estimator.fit(
        ml_dataset[columns], ml_dataset[config.TARGET]
    )
    predictions = np.asarray(estimator.predict(ml_dataset[columns]), dtype=float)
    assert predictions.shape == (len(ml_dataset),)
    assert np.all(predictions > 0)


def test_lightgbm_family_slug_is_stable() -> None:
    """L'identifiant du candidat LightGBM est celui attendu par la sélection."""
    slugs = [spec.slug for spec in models.build_models(2)]
    assert "lightgbm_log1p" in slugs


def test_preprocessor_keeps_missing_value_indicator(ml_dataset: pd.DataFrame) -> None:
    """Le pré-traitement s'applique aux features construites et impute sans masquer."""
    frame = ml_dataset.copy()
    frame.loc[0, "bedrooms"] = np.nan
    built = features.FeatureBuilder().fit_transform(frame[training.features_columns()])
    preprocessed = models.make_preprocessor().fit_transform(built)

    assert preprocessed.shape[0] == len(ml_dataset)
    # 3 catégorielles one-hot + numériques imputés et centrés + indicateur de manquant
    assert preprocessed.shape[1] >= len(features.MODEL_FEATURES)
    assert np.all(np.isfinite(preprocessed))
