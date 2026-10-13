"""Tests du protocole d'entraînement et de sélection (Phase 6)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.src import config, models, training


def _small_specs(seed: int = 1) -> list[models.ModelSpec]:
    return [
        spec
        for spec in models.build_models(seed, include_lightgbm=False)
        if spec.slug in ("linear_brut", "ridge_log1p")
    ]


def test_features_columns_exclude_the_target() -> None:
    columns = training.features_columns()
    assert isinstance(columns, list)
    assert config.TARGET not in columns
    assert set(columns) == set(config.FEATURE_COLUMNS)


def test_reference_threshold_is_recomputed_on_the_split(ml_dataset: pd.DataFrame) -> None:
    threshold, baselines = training.reference_threshold(ml_dataset, seed=11)
    assert set(baselines) == {"baseline_global", "baseline_city", "baseline_neighborhood"}
    assert threshold["baseline"] == "baseline_neighborhood"
    # la borne basse de l'IC est nécessairement sous la MAE ponctuelle
    assert threshold["mae_borne_basse_ic"] < threshold["mae_validation"]
    assert threshold["mae_borne_haute_ic"] > threshold["mae_borne_basse_ic"]
    assert threshold["gain_relatif_a_demontrer_pct"] > 0


def test_compare_candidates_evaluates_every_candidate(ml_dataset: pd.DataFrame) -> None:
    comparison = training.compare_candidates(ml_dataset, seed=11, specs=_small_specs())
    parts = comparison["parts"]
    assert {name: len(part) for name, part in parts.items()} == {
        "train": 210,
        "validation": 45,
        "test": 45,
    }
    for slug, result in comparison["candidats"].items():
        assert result["slug"] == slug
        for split_name in ("train", "validation", "test"):
            metrics = result["metriques"][split_name]
            assert metrics["n"] == len(parts[split_name])
            assert metrics["mae"] >= 0
            assert metrics["temps_prediction_s"] >= 0
        assert result["entrainement_s"] >= 0
        assert result["predictions"]["validation"].shape == (45,)


def test_selection_picks_the_lowest_validation_mae(ml_dataset: pd.DataFrame) -> None:
    comparison = training.compare_candidates(ml_dataset, seed=11, specs=_small_specs())
    threshold, _ = training.reference_threshold(ml_dataset, seed=11)
    selection = training.select_best(comparison["candidats"], threshold)

    best_mae = min(
        result["metriques"]["validation"]["mae"] for result in comparison["candidats"].values()
    )
    assert selection["mae_validation"] == best_mae
    slug = selection["slug"]
    assert selection["bat_le_seuil_validation"] == (
        comparison["candidats"][slug]["metriques"]["validation"]["mae"]
        < threshold["mae_borne_basse_ic"]
    )
    assert selection["classement"][0]["slug"] == slug
    assert {
        "slug",
        "label",
        "famille",
        "cible",
        "complexite",
        "interpretabilite",
        "mae_train",
        "mae_validation",
        "medae_validation",
        "mae_test",
        "entrainement_s",
    } <= set(selection["classement"][0])


def test_selection_rule_is_documented() -> None:
    rule = training.selection_rule({"mae_borne_basse_ic": 79_773})
    assert "79" in rule
    assert "médian" in rule
    assert "graines" in rule


def test_median_gain_is_the_middle_of_the_ordered_gains() -> None:
    assert training.median_gain_pct({"executions": [{"gain_validation_pct": 3.0}]}) == 3.0
    assert (
        training.median_gain_pct(
            {"executions": [{"gain_validation_pct": gain} for gain in (10.0, 1.0, 5.0)]}
        )
        == 5.0
    )
    assert (
        training.median_gain_pct(
            {"executions": [{"gain_validation_pct": gain} for gain in (10.0, 20.0)]}
        )
        == 15.0
    )
    assert training.median_gain_pct({"executions": []}) is None


def test_selection_uses_the_median_gain_across_seeds() -> None:
    """Un candidat meilleur sur 2 graines sur 3 doit l'emporter, même moins bon ici."""
    candidates = {
        "reference_only": {
            "slug": "reference_only",
            "label": "celui de la graine de référence",
            "famille": "test",
            "cible_transformee": "brut",
            "complexite": "faible",
            "interpretabilite": "bonne",
            "metriques": {
                "train": {"mae": 10.0},
                "validation": {"mae": 100.0, "medae": 8.0, "r2": 0.5},
                "test": {"mae": 110.0, "medae": 9.0},
            },
            "entrainement_s": 0.1,
        },
        "steady": {
            "slug": "steady",
            "label": "celui stable sur toutes les graines",
            "famille": "test",
            "cible_transformee": "brut",
            "complexite": "faible",
            "interpretabilite": "bonne",
            "metriques": {
                "train": {"mae": 12.0},
                "validation": {"mae": 110.0, "medae": 9.0, "r2": 0.5},
                "test": {"mae": 115.0, "medae": 10.0},
            },
            "entrainement_s": 0.1,
        },
    }
    threshold = {"mae_borne_basse_ic": 95.0, "mae_validation": 120.0}
    robustness = {
        "reference_only": {
            "executions": [
                {"graine": 1, "gain_validation_pct": 20.0},
                {"graine": 2, "gain_validation_pct": 2.0},
                {"graine": 3, "gain_validation_pct": 1.0},
            ]
        },
        "steady": {
            "executions": [
                {"graine": 1, "gain_validation_pct": 10.0},
                {"graine": 2, "gain_validation_pct": 12.0},
                {"graine": 3, "gain_validation_pct": 11.0},
            ]
        },
    }
    selection = training.select_best(candidates, threshold, robustness)
    assert selection["slug"] == "steady"
    assert selection["gain_median_pct"] == 11.0
    # rang de la graine de référence conservé pour que le rapport reste lisible
    assert selection["rang_graine_reference"] == 2
    assert selection["classement"][0]["slug"] == "reference_only"


def test_candidates_absent_from_robustness_cannot_win() -> None:
    """Régression : un candidat hors présélection ne doit pas lever de KeyError."""

    def candidate(slug: str, mae: float) -> dict[str, object]:
        return {
            "slug": slug,
            "label": slug,
            "famille": "test",
            "cible_transformee": "brut",
            "complexite": "faible",
            "interpretabilite": "bonne",
            "metriques": {
                "train": {"mae": 1.0},
                "validation": {"mae": mae, "medae": 8.0, "r2": 0.5},
                "test": {"mae": 12.0, "medae": 9.0},
            },
            "entrainement_s": 0.1,
        }

    candidates = {
        "pas_robuste": candidate("pas_robuste", 10.0),  # meilleur en graine unique
        "robuste": candidate("robuste", 30.0),
    }
    robustness = {
        "robuste": {"executions": [{"graine": 1, "gain_validation_pct": 15.0}]},
        # `pas_robuste` est volontairement absent de la robustesse (hors présélection).
    }
    threshold = {"mae_borne_basse_ic": 5.0, "mae_validation": 20.0}
    selection = training.select_best(candidates, threshold, robustness)
    assert selection["slug"] == "robuste"
    assert selection["gain_median_pct"] == 15.0
    assert selection["rang_graine_reference"] == 2


def test_a_single_seed_candidate_is_kept_when_no_robustness_exists() -> None:
    reference = {
        "slug": "pas_robuste",
        "label": "hors robustesse",
        "famille": "test",
        "cible_transformee": "brut",
        "complexite": "faible",
        "interpretabilite": "bonne",
        "metriques": {
            "train": {"mae": 1.0},
            "validation": {"mae": 10.0, "medae": 8.0, "r2": 0.5},
            "test": {"mae": 12.0, "medae": 9.0},
        },
        "entrainement_s": 0.1,
    }
    threshold = {"mae_borne_basse_ic": 5.0, "mae_validation": 20.0}
    selection = training.select_best({"pas_robuste": reference}, threshold, {})
    assert selection["slug"] == "pas_robuste"
    assert selection["gain_median_pct"] is None


def test_shortlist_keeps_the_best_of_the_reference_seed(ml_dataset: pd.DataFrame) -> None:
    comparison = training.compare_candidates(ml_dataset, seed=11, specs=_small_specs())
    shortlist = training.shortlist(candidates=comparison["candidats"], size=2)
    assert shortlist == ["linear_brut", "ridge_log1p"]


def test_a_linear_target_is_beaten_by_a_linear_model() -> None:
    """Sanity check : quand le prix est exactement linéaire, le modèle doit gagner."""
    frame = pd.DataFrame(
        {
            "listing_key": [f"x{index}" for index in range(60)],
            "city": ["Douala"] * 60,
            "neighborhood": ["Bali"] * 60,
            "property_type": ["apartment"] * 60,
            "bedrooms": [1 + index % 4 for index in range(60)],
            "bathrooms": [1 + index % 3 for index in range(60)],
            "target_rent_price": [
                50_000 + (1 + index % 4) * 25_000 + (1 + index % 3) * 5_000
                for index in range(60)
            ],
            "price_is_bound": False,
            "is_republication": False,
            "outlier_flags": "",
            "neighborhood_recognized": True,
            "collected_at": "2026-10-09T07:05:36+00:00",
            "posted_at": None,
        }
    )
    specs = [
        spec
        for spec in models.build_models(3, include_lightgbm=False)
        if spec.slug == "linear_brut"
    ]
    comparison = training.compare_candidates(frame, seed=3, specs=specs)
    result = comparison["candidats"]["linear_brut"]
    assert result["metriques"]["validation"]["mae"] < 1_000


def test_robustness_compares_each_seed_to_its_own_baseline(
    ml_dataset: pd.DataFrame,
) -> None:
    summary = training.robustness(
        ml_dataset,
        slugs=["linear_brut"],
        seeds=(1, 2),
        include_lightgbm=False,
    )
    block = summary["linear_brut"]
    assert block["graines"] == [1, 2]
    assert block["nb_graines"] == 2
    assert len(block["executions"]) == 2
    for run in block["executions"]:
        baseline = run["baseline_mae_validation"]
        assert baseline > 0
        expected = 100 * (baseline - run["mae_validation"]) / baseline
        assert run["gain_validation_pct"] == pytest.approx(expected, abs=0.01)
        assert isinstance(run["bat_la_baseline"], bool)
    assert 0 <= block["nb_graines_battant_la_baseline"] <= 2
    assert 0 <= block["nb_graines_battant_le_seuil"] <= 2


def test_errors_summary_reports_relative_coverage() -> None:
    # erreurs relatives de 10 % et 50 % : seule la première est à ±20 %.
    summary = training.errors_summary([100_000, 200_000], [110_000, 300_000])
    assert summary["mae"] == 55_000
    assert summary["medae"] == 55_000
    assert summary["part_a_moins_de_20_pct"] == 50.0


def test_segment_block_flags_small_segments(ml_dataset: pd.DataFrame) -> None:
    comparison = training.compare_candidates(ml_dataset, seed=11, specs=_small_specs())
    result = comparison["candidats"]["linear_brut"]
    segments = training.segment_block(
        result, comparison["parts"], min_n=30, split_name="validation"
    )
    assert set(segments) == {
        "ville",
        "type_de_logement",
        "nombre_de_chambres",
        "niveau_de_prix",
        "quartier",
    }
    for records in segments.values():
        for record in records:
            assert record["n"] >= 1
            assert isinstance(record["sous_seuil_de_publication"], bool)
            assert np.isfinite(record["mae"])
