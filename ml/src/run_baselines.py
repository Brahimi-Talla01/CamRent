"""Évalue les baselines de la Phase 5 et produit les métriques + le rapport.

Enchaînement : chargement du mart ML → scénarios → séparation train/validation/
test → entraînement des baselines → métriques globales, par segment et
incertitude → seuil de référence. Le JSON produit (`ml/artifacts/`) est
**déterministe** (aucun horodatage) : il sert de comparaison de rejeu ; le
markdown, lui, est daté.

Aucune exclusion silencieuse : les scénarios restreints sont des analyses de
sensibilité explicitement étiquetées, le scénario principal conserve toutes les
observations.
"""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn

from . import baselines, config, data, evaluation, report, split


def _metrics_for_frame(
    baseline: baselines.Baseline,
    frame: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Métriques et répartition des niveaux de prédiction pour un ensemble."""
    values, levels = baseline.predict_with_levels(frame)
    metrics = evaluation.regression_metrics(frame[config.TARGET], values)
    unique, counts = np.unique(levels, return_counts=True)
    return metrics, {str(level): int(count) for level, count in zip(unique, counts, strict=True)}


def _segment_block(
    baseline: baselines.Baseline,
    frame: pd.DataFrame,
    *,
    edges: np.ndarray,
    min_n: int,
) -> dict[str, list[dict[str, Any]]]:
    """Segments d'évaluation : ville, type, chambres, niveau de prix, quartier."""
    truth = frame[config.TARGET]
    predicted = baseline.predict(frame)
    neighborhoods = frame["city"].astype(str) + " / " + frame["neighborhood"].astype(str)
    return {
        "ville": evaluation.segment_metrics(
            truth, predicted, frame["city"], min_n=min_n, segment_column="ville"
        ),
        "type_de_logement": evaluation.segment_metrics(
            truth,
            predicted,
            frame["property_type"],
            min_n=min_n,
            segment_column="type_de_logement",
        ),
        "nombre_de_chambres": evaluation.segment_metrics(
            truth,
            predicted,
            evaluation.bedrooms_labels(frame["bedrooms"]),
            min_n=min_n,
            segment_column="nombre_de_chambres",
        ),
        "niveau_de_prix": evaluation.segment_metrics(
            truth,
            predicted,
            evaluation.price_level_labels(truth, edges),
            min_n=min_n,
            segment_column="niveau_de_prix",
        ),
        "quartier": evaluation.segment_metrics(
            truth,
            predicted,
            neighborhoods,
            min_n=min_n,
            segment_column="quartier",
        ),
    }


def _split_description(parts: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Décrit chaque ensemble : effectifs par ville et marqueurs de qualité."""
    description: dict[str, Any] = {}
    for name, frame in parts.items():
        flags = frame["outlier_flags"].fillna("").astype(str).str.strip()
        description[name] = {
            "n_observations": int(len(frame)),
            "part": round(100.0 * len(frame) / sum(len(part) for part in parts.values()), 2),
            "par_ville": {
                str(city): int(count) for city, count in frame["city"].value_counts().items()
            },
            "republications": int(frame["is_republication"].astype(bool).sum()),
            "prix_borne": int(frame["price_is_bound"].astype(bool).sum()),
            "aberrations": int((flags != "").sum()),
            "quartiers_distincts": int(frame["neighborhood"].nunique()),
        }
    return description


def evaluate_scenario(
    frame: pd.DataFrame,
    *,
    name: str,
    min_n: int,
    seed: int,
) -> dict[str, Any]:
    """Évalue les trois baselines sur un scénario complet."""
    parts = split.split_dataset(frame, seed=seed)
    edges = evaluation.price_quartile_edges(parts["train"][config.TARGET])

    blocks: dict[str, Any] = {}
    for baseline in baselines.build_baselines():
        baseline.fit(parts["train"])
        metrics: dict[str, Any] = {}
        levels: dict[str, Any] = {}
        for split_name, part in parts.items():
            split_metrics, split_levels = _metrics_for_frame(baseline, part)
            metrics[split_name] = split_metrics
            levels[split_name] = split_levels
        blocks[baseline.name] = {
            "definition": baseline.describe()["definition"],
            "parametres": baseline.describe(),
            "metriques": metrics,
            "niveaux_de_prediction": levels,
            "ic_mae_validation": evaluation.bootstrap_mae_ci(
                parts["validation"][config.TARGET],
                baseline.predict(parts["validation"]),
                seed=seed,
            ),
            "segments": {
                split_name: _segment_block(
                    baseline,
                    part,
                    edges=edges,
                    min_n=min_n,
                )
                for split_name, part in parts.items()
                if split_name in ("validation", "test")
            },
        }

    return {
        "nom": name,
        "description": data.SCENARIOS.get(name, ""),
        "n_observations": int(len(frame)),
        "taille_par_ensemble": _split_description(parts),
        "baselines": blocks,
        "seuil_reference_validation": _reference_threshold(blocks),
    }


def _reference_threshold(blocks: dict[str, Any]) -> dict[str, Any]:
    """Seuil de référence : borne basse de l'IC bootstrap de la meilleure baseline.

    Un gain inférieur à cette borne n'est pas distinguable du bruit
    d'échantillonnage : c'est la règle de décision annoncée en Phase 6.
    """
    best_name = min(
        blocks,
        key=lambda name: blocks[name]["metriques"]["validation"]["mae"],
    )
    best = blocks[best_name]
    validation = best["metriques"]["validation"]
    interval = best["ic_mae_validation"]
    threshold = interval["mae_borne_basse"]
    gain = validation["mae"] - threshold
    return {
        "baseline": best_name,
        "mae_validation": validation["mae"],
        "mae_test": best["metriques"]["test"]["mae"],
        "mae_borne_basse_ic": threshold,
        "mae_borne_haute_ic": interval["mae_borne_haute"],
        "gain_absolu_a_demontrer_fcfa": gain,
        "gain_relatif_a_demontrer_pct": round(100.0 * gain / validation["mae"], 2),
    }


def _worst_segments(
    blocks: dict[str, Any],
    *,
    minimum_n: int,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Segments où la meilleure baseline échoue le plus (MAE la plus élevée)."""
    best_name = min(
        blocks,
        key=lambda name: blocks[name]["metriques"]["validation"]["mae"],
    )
    rows: list[dict[str, Any]] = []
    for family, segments in blocks[best_name]["segments"]["validation"].items():
        for segment in segments:
            label_column = next(iter(segment))
            if segment["n"] < minimum_n:
                continue
            rows.append(
                {
                    "famille": family,
                    "segment": segment[label_column],
                    "n": segment["n"],
                    "mae": segment["mae"],
                    "baseline": best_name,
                }
            )
    rows.sort(key=lambda item: (item["mae"], item["n"]), reverse=True)
    return rows[:limit]


def build_metrics(
    frame: pd.DataFrame,
    *,
    min_n: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Construit l'ensemble des métriques (structure sérialisable en JSON)."""
    min_n = config.MIN_SEGMENT_N if min_n is None else min_n
    seed = config.RANDOM_SEED if seed is None else seed

    scenarios = data.scenario_frames(frame)
    evaluated = {
        name: evaluate_scenario(scenario_frame, name=name, min_n=min_n, seed=seed)
        for name, scenario_frame in scenarios.items()
    }
    primary = evaluated[data.PRIMARY_SCENARIO]
    best_name = min(
        primary["baselines"],
        key=lambda name: primary["baselines"][name]["metriques"]["validation"]["mae"],
    )
    return {
        "meta": {
            "phase": "5 — Baseline ML",
            "source": config.SOURCE_REFERENCE,
            "cible": config.TARGET,
            "devise": config.CURRENCY,
            "features": list(config.FEATURE_COLUMNS),
            "drapeaux_qualite": list(config.FLAG_COLUMNS),
            "scenario_principal": data.PRIMARY_SCENARIO,
            "scenarios": data.SCENARIOS,
            "graine": seed,
            "proportions": config.SPLIT_SHARES,
            "iterations_bootstrap": config.BOOTSTRAP_ITERATIONS,
            "alpha_bootstrap": config.BOOTSTRAP_ALPHA,
            "effectif_minimum_par_segment": min_n,
            "versions": {
                "python": platform.python_version(),
                "pandas": pd.__version__,
                "numpy": np.__version__,
                "scikit_learn": sklearn.__version__,
            },
            "chronologie": data.describe_chronology(frame),
            "qualite": data.describe_quality(frame),
        },
        "scenarios": evaluated,
        "conclusion": {
            "meilleure_baseline": best_name,
            "seuil_reference": primary["seuil_reference_validation"],
            "segments_les_plus_difficiles": _worst_segments(
                primary["baselines"], minimum_n=min_n
            ),
        },
    }


def run(
    database_url: str | None = None,
    *,
    artifacts_dir: Path | None = None,
    report_path: Path | None = None,
    metrics_path: Path | None = None,
) -> dict[str, Any]:
    """Exécute la Phase 5 de bout en bout et écrit les artefacts."""
    frame = data.load_ml_dataset(database_url)
    metrics = build_metrics(frame)

    artifacts_dir = artifacts_dir or config.ARTIFACTS_DIR
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_path or artifacts_dir / config.METRICS_FILENAME
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report_path = report_path or config.REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    report_path.write_text(
        report.render_report(metrics, generated_at=generated_at), encoding="utf-8"
    )

    metrics["artefacts"] = {
        "metriques": str(metrics_path),
        "rapport": str(report_path),
    }
    return metrics
