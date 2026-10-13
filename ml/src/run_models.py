"""Orchestration de la Phase 6 : comparer, retenir, valider, expliquer, sauvegarder.

Enchaînement :

1. séparation de référence (identique à la Phase 5) et seuil recalculé ;
2. comparaison de tous les candidats (familles × transformation de cible) ;
3. sélection selon la règle documentée + robustesse sur d'autres graines ;
4. fourchette de prédiction : deux méthodes calibrées puis comparées ;
5. performance par segment, explicabilité, exemple expliqué ;
6. sauvegarde du modèle retenu et de ses métadonnées ;
7. rapport markdown entièrement dérivé des résultats.

Le dictionnaire retourné ne contient que des valeurs sérialisables : le modèle
lui-même est écrit sur disque (`ml/models/`, ignoré par git).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import (
    config,
    data,
    features,
    interpretability,
    model_report,
    persistence,
    training,
    uncertainty,
)


def _example_row(frame: pd.DataFrame) -> pd.Series:
    """Ligne d'exemple reproductible : prix observé le plus proche de la médiane."""
    median = float(frame[config.TARGET].median())
    position = int((frame[config.TARGET] - median).abs().to_numpy().argmin())
    return frame.iloc[position]


def _interval_for_row(
    interval_model: Any,
    row: pd.Series,
    prediction: float,
) -> tuple[float, float]:
    """Bornes de l'intervalle pour une ligne, selon la méthode retenue."""
    if isinstance(interval_model, uncertainty.ConformalInterval):
        low, high = interval_model.bounds(np.array([prediction], dtype=float))
        return float(low[0]), float(high[0])
    low, high = interval_model.bounds(row.to_frame().T)
    return float(low[0]), float(high[0])


def build_results(
    frame: pd.DataFrame,
    *,
    seed: int | None = None,
    include_lightgbm: bool = True,
    min_n: int | None = None,
    persist: bool = True,
    models_dir: Path | None = None,
) -> dict[str, Any]:
    """Construit tous les résultats de la Phase 6 (sérialisables en JSON)."""
    seed = config.RANDOM_SEED if seed is None else seed
    min_n = config.MIN_SEGMENT_N if min_n is None else min_n

    threshold, measured_baselines = training.reference_threshold(frame, seed=seed)
    comparison = training.compare_candidates(
        frame, seed=seed, include_lightgbm=include_lightgbm
    )
    parts = comparison["parts"]
    candidates = comparison["candidats"]

    # Sélection en deux temps : présélection sur la graine de référence, puis
    # départage sur le gain **médian** face à la baseline recalculée sur chaque
    # graine. Choisir sur une seule séparation reviendrait à choisir du bruit.
    shortlisted = training.shortlist(candidates)
    robustness = training.robustness(
        frame, slugs=shortlisted, seeds=config.ROBUSTNESS_SEEDS, include_lightgbm=include_lightgbm
    )
    selection = training.select_best(candidates, threshold, robustness)
    retained = candidates[selection["slug"]]
    retained_robustness = robustness.get(selection["slug"], {})
    selection["preselection"] = shortlisted
    selection["robustesse"] = {
        "graines": retained_robustness.get("graines", []),
        "nb_graines": retained_robustness.get("nb_graines", 0),
        "nb_graines_battant_le_seuil": retained_robustness.get("nb_graines_battant_le_seuil", 0),
        "nb_graines_battant_la_baseline": retained_robustness.get(
            "nb_graines_battant_la_baseline", 0
        ),
        "gain_validation_moyen_pct": retained_robustness.get("gain_validation_moyen_pct"),
        "gain_validation_median_pct": retained_robustness.get("gain_validation_median_pct"),
        "gain_validation_min_pct": retained_robustness.get("gain_validation_min_pct"),
        "mae_validation_moyenne": retained_robustness.get("mae_validation_moyenne"),
    }
    selection["critere_selection"] = training.selection_rule(threshold)

    intervals = uncertainty.compare_methods(
        parts, predictions=retained["predictions"], seed=seed
    )
    interval_model = uncertainty.retained_interval(
        intervals["methode_retenue"], parts, predictions=retained["predictions"], seed=seed
    )

    importance = interpretability.permutation_importance_table(
        retained["modele"], parts["validation"], seed=seed
    )
    # Dépendance partielle limitée aux variables présentes dans le mart : les
    # features dérivées (`logements_dans_quartier`) sont recalculées par le
    # pipeline, les permuter sur le mart n'aurait aucun effet (piège classique).
    dependence = {
        feature: interpretability.partial_dependence_table(
            retained["modele"], parts["test"], feature
        )
        for feature in ("bedrooms", "bathrooms")
    }

    example_row = _example_row(parts["test"])
    example_inputs = example_row.to_frame().T[list(training.features_columns())]
    example_prediction = float(
        np.asarray(retained["modele"].predict(example_inputs), dtype=float)[0]
    )
    example_interval = _interval_for_row(interval_model, example_row, example_prediction)
    example = interpretability.explain_prediction(
        retained["modele"],
        example_row,
        parts["train"],
        interval=example_interval,
        min_n=min_n,
    )

    artifacts: dict[str, str] = {}
    if persist:
        metadata = {
            "nom": config.MODEL_ARTIFACT_NAME,
            "famille": retained["famille"],
            "cible_transformee": retained["cible_transformee"],
            "features": list(features.MODEL_FEATURES),
            "hyperparametres": retained["hyperparametres"],
            "graine": seed,
            "metriques": retained["metriques"],
            "seuil_phase_5": threshold,
            "intervalle": {
                **interval_model.describe(),
                "couverture_test_pct": intervals["methodes"][intervals["methode_retenue"]][
                    "test"
                ]["couverture_pct"],
            },
            "versions": persistence.versions(),
        }
        artifacts = persistence.save_model(
            retained["modele"], metadata, models_dir=models_dir, interval=interval_model
        )

    return {
        "meta": {
            "phase": "6 — Modèles ML",
            "source": config.SOURCE_REFERENCE,
            "cible": config.TARGET,
            "devise": config.CURRENCY,
            "graine": seed,
            "proportions": config.SPLIT_SHARES,
            "features": list(features.MODEL_FEATURES),
            "features_ecartees": features.EXCLUDED_FEATURES,
            "graines_robustesse": list(config.ROBUSTNESS_SEEDS),
            "effectif_minimum_par_segment": min_n,
            "alpha_intervalle": config.INTERVAL_ALPHA,
            "versions": persistence.versions(),
            "qualite": data.describe_quality(frame),
            "chronologie": data.describe_chronology(frame),
        },
        "seuil_reference": threshold,
        "baselines": measured_baselines,
        "candidats": {
            slug: {
                key: value
                for key, value in result.items()
                if key not in ("modele", "predictions")
            }
            for slug, result in candidates.items()
        },
        "selection": selection,
        "robustesse": robustness,
        "segments": {
            "validation": training.segment_block(
                retained, parts, min_n=min_n, split_name="validation"
            ),
            "test": training.segment_block(retained, parts, min_n=min_n, split_name="test"),
        },
        "erreurs_test": training.errors_summary(
            parts["test"][config.TARGET], retained["predictions"]["test"]
        ),
        "intervalles": intervals,
        "explicabilite": {
            "importance_globale": importance,
            "dependance_partielle": dependence,
            "exemple": example,
        },
        "artefacts": artifacts,
    }


def run(
    database_url: str | None = None,
    *,
    report_path: Path | None = None,
    metrics_path: Path | None = None,
    models_dir: Path | None = None,
    include_lightgbm: bool = True,
    persist: bool = True,
) -> dict[str, Any]:
    """Exécute la Phase 6 de bout en bout et écrit les artefacts."""
    frame = data.load_ml_dataset(database_url)
    results = build_results(
        frame,
        include_lightgbm=include_lightgbm,
        persist=persist,
        models_dir=models_dir,
    )

    models_dir = models_dir or config.MODELS_DIR
    metrics_path = metrics_path or models_dir / "model_selection.json"
    report_path = report_path or config.MODEL_REPORT_PATH

    results["artefacts"] = {
        **results.get("artefacts", {}),
        "selection": str(metrics_path),
        "rapport": str(report_path),
    }

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    report_path.write_text(
        model_report.render_report(results, generated_at=generated_at), encoding="utf-8"
    )
    return results
