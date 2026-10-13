"""Tests de l'explicabilité et de la persistance du modèle (Phase 6)."""

from __future__ import annotations

import json

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

from ml.src import config, interpretability, models, persistence, uncertainty


@pytest.fixture
def fitted_model(ml_dataset):
    """Modèle linéaire ajusté sur le dataset synthétique (cible brute)."""
    estimator = models.build_pipeline(LinearRegression(), target_transform="brut")
    return estimator.fit(
        ml_dataset[list(config.FEATURE_COLUMNS)], ml_dataset[config.TARGET]
    )


def test_permutation_table_covers_every_feature_and_is_sorted(
    fitted_model, ml_dataset
) -> None:
    table = interpretability.permutation_importance_table(
        fitted_model, ml_dataset, repeats=3, seed=7
    )
    assert [row["feature"] for row in table] != []
    assert {row["feature"] for row in table} == set(config.FEATURE_COLUMNS)
    values = [row["erreur_mediane_supplementaire_moyenne"] for row in table]
    assert values == sorted(values, reverse=True)
    for row in table:
        assert row["n"] == len(ml_dataset)
        assert row["erreur_mediane_supplementaire_ecart_type"] >= 0
    # Une ville et un nombre de chambres séparent vraiment les loyers : au moins
    # une variable doit porter une importance strictement positive.
    assert values[0] > 0


def test_the_permutation_score_reacts_to_a_useless_column(fitted_model, ml_dataset) -> None:
    """Une feature constante ne peut pas dégrader la prévision typique."""
    frame = ml_dataset.copy()
    frame["neighborhood"] = "constant"
    table = interpretability.permutation_importance_table(
        fitted_model, frame, repeats=3, seed=7
    )
    constant_row = next(row for row in table if row["feature"] == "neighborhood")
    assert constant_row["erreur_mediane_supplementaire_moyenne"] == 0


def test_partial_dependence_covers_observed_values(fitted_model, ml_dataset) -> None:
    table = interpretability.partial_dependence_table(fitted_model, ml_dataset, "bedrooms")
    observed = sorted(set(ml_dataset["bedrooms"]))
    assert [row["valeur"] for row in table] == observed
    assert all(row["n"] == len(ml_dataset) for row in table)
    # Plus de chambres doit valoir plus cher sur ce jeu de données construit ainsi.
    assert table[-1]["prediction_mediane"] > table[0]["prediction_mediane"]


def test_partial_dependence_rejects_unknown_feature(fitted_model, ml_dataset) -> None:
    with pytest.raises(ValueError, match="Variable inconnue"):
        interpretability.partial_dependence_table(fitted_model, ml_dataset, "surface")


def test_local_market_context_counts_and_publishes(ml_dataset) -> None:
    row = ml_dataset.iloc[0]
    context = interpretability.local_market_context(ml_dataset, row, min_n=2)
    assert context["ville"] == row["city"]
    assert context["n_ville"] > 0
    assert context["mediane_ville"] is not None
    assert context["publiee"] == (context["n_quartier_type"] >= 2)


def test_unknown_group_is_reported_without_median(ml_dataset) -> None:
    row = ml_dataset.iloc[0].copy()
    row["neighborhood"] = "Quartier Inexistant"
    context = interpretability.local_market_context(ml_dataset, row, min_n=1)
    assert context["n_quartier_type"] == 0
    assert context["mediane_quartier_type"] is None
    assert context["publiee"] is False


def test_explain_prediction_returns_value_interval_and_gap(fitted_model, ml_dataset) -> None:
    row = ml_dataset.iloc[3]
    explanation = interpretability.explain_prediction(
        fitted_model, row, ml_dataset, interval=(50_000.0, 150_000.0), min_n=2
    )
    assert explanation["prevision"] > 0
    assert explanation["intervalle"] == [50_000, 150_000]
    assert explanation["marche_local"]["ville"] == row["city"]
    assert explanation["caracteristiques"]["chambres"] == int(row["bedrooms"])
    assert "ecart_vs_mediane_quartier_pct" in explanation


def test_explain_prediction_handles_a_missing_group(fitted_model, ml_dataset) -> None:
    row = ml_dataset.iloc[1].copy()
    row["neighborhood"] = "Fantome"
    explanation = interpretability.explain_prediction(fitted_model, row, ml_dataset)
    assert "ecart_vs_mediane_quartier_pct" not in explanation
    assert explanation["marche_local"]["mediane_quartier_type"] is None


def test_versions_and_metadata_validation() -> None:
    version_block = persistence.versions()
    assert {"python", "pandas", "numpy", "scikit_learn"} <= set(version_block)
    with pytest.raises(ValueError, match="Métadonnées incomplètes"):
        persistence.validate_metadata({"nom": "x"})
    complete = {key: None for key in config.MODEL_METADATA_KEYS}
    persistence.validate_metadata(complete)  # ne lève pas


def test_save_model_round_trips_predictions(fitted_model, ml_dataset, tmp_path) -> None:
    frame = ml_dataset[list(config.FEATURE_COLUMNS)]
    metadata = {key: None for key in config.MODEL_METADATA_KEYS}
    metadata["nom"] = "test_artifact"
    paths = persistence.save_model(
        fitted_model, metadata, models_dir=tmp_path, name="test_artifact"
    )

    reloaded = persistence.load_model(paths["modele"])
    np.testing.assert_allclose(reloaded.predict(frame), fitted_model.predict(frame))
    payload = persistence.load_metadata(paths["metadonnees"])
    assert payload["nom"] == "test_artifact"
    assert json.loads((tmp_path / "test_artifact.json").read_text(encoding="utf-8")) == payload


def test_interval_survives_the_round_trip(fitted_model, tmp_path) -> None:
    """L'intervalle calibré doit être réutilisable tel quel (sans recalibrer)."""
    interval = uncertainty.ConformalInterval(alpha=0.2).fit([100.0, 200.0], [110.0, 190.0])
    metadata = {key: None for key in config.MODEL_METADATA_KEYS}
    paths = persistence.save_model(
        fitted_model,
        metadata,
        models_dir=tmp_path,
        name="artefact_intervalle",
        interval=interval,
    )
    assert "intervalle" in paths
    reloaded = persistence.load_interval(paths["intervalle"])
    expected_low, expected_high = interval.bounds(np.array([150.0]))
    low, high = reloaded.bounds(np.array([150.0]))
    np.testing.assert_allclose(low, expected_low)
    np.testing.assert_allclose(high, expected_high)
    assert reloaded.describe() == interval.describe()


def test_quantile_interval_round_trips_and_keeps_bounds_valid(ml_dataset, tmp_path) -> None:
    """La méthode retenue (régression quantile) doit rester utilisable après rechargement."""
    inputs = ml_dataset[list(config.FEATURE_COLUMNS)]
    truth = ml_dataset[config.TARGET]
    interval = uncertainty.QuantileRegressionInterval(alpha=0.2, seed=5).fit(inputs, truth)

    metadata = {key: None for key in config.MODEL_METADATA_KEYS}
    paths = persistence.save_model(
        LinearRegression(),
        metadata,
        models_dir=tmp_path,
        name="artefact_quantile",
        interval=interval,
    )
    reloaded = persistence.load_interval(paths["intervalle"])
    low, high = reloaded.bounds(inputs)
    expected_low, expected_high = interval.bounds(inputs)
    np.testing.assert_allclose(low, expected_low)
    np.testing.assert_allclose(high, expected_high)
    report = uncertainty.coverage_report(truth, low, high)
    assert 0 <= report["couverture_pct"] <= 100
    assert np.all(low >= uncertainty.MIN_RENT)
    assert np.all(low <= high)


def test_missing_artifacts_raise_a_clear_error(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="Modèle introuvable"):
        persistence.load_model(tmp_path / "absent.joblib")
    with pytest.raises(FileNotFoundError, match="Métadonnées introuvables"):
        persistence.load_metadata(tmp_path / "absent.json")
    with pytest.raises(FileNotFoundError, match="Intervalle introuvable"):
        persistence.load_interval(tmp_path / "absent.joblib")
