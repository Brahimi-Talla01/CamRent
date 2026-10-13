"""Entraînement et comparaison des candidats (Phase 6).

Protocole (identique pour tous : sinon la comparaison ne vaut rien) :

1. **même séparation** que la Phase 5 (graine, 70/15/15) ;
2. seuil de référence **recalculé** ici, sur la même séparation, plutôt que lu
   dans un artefact : bornes basses de l'intervalle de confiance bootstrap de la
   meilleure baseline ;
3. évaluation de chaque candidat : MAE / RMSE / R² / MedAE sur entraînement,
   validation et test, plus temps d'entraînement et de prédiction ;
4. sélection sur la MAE de validation (métrique principale), avec confirmation
   sur la MedAE et sur d'**autres graines** — la Phase 5 a montré que la MAE est
   instable sous cette distribution.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

from . import baselines, config, evaluation, models, split


def _fit_evaluate(spec: models.ModelSpec, parts: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Entraîne un candidat sur `train` et l'évalue sur les trois ensembles."""
    estimator = _clone(spec.estimator)
    started = time.perf_counter()
    estimator.fit(parts["train"][features_columns()], parts["train"][config.TARGET])
    fit_seconds = time.perf_counter() - started

    metrics: dict[str, Any] = {}
    predictions: dict[str, np.ndarray] = {}
    for name in ("train", "validation", "test"):
        started = time.perf_counter()
        predicted = estimator.predict(parts[name][features_columns()])
        elapsed = time.perf_counter() - started
        predictions[name] = np.asarray(predicted, dtype=float)
        block = evaluation.regression_metrics(parts[name][config.TARGET], predicted)
        block["temps_prediction_s"] = round(elapsed, 4)
        metrics[name] = block

    return {
        "slug": spec.slug,
        "label": spec.label,
        "famille": spec.famille,
        "cible_transformee": spec.target_transform,
        "complexite": spec.complexite,
        "interpretabilite": spec.interpretabilite,
        "hyperparametres": _params(spec),
        "entrainement_s": round(fit_seconds, 4),
        "metriques": metrics,
        "predictions": predictions,
        "modele": estimator,
    }


def features_columns() -> list[str]:
    """Colonnes d'entrée lues dans le mart (jamais la cible).

    Renvoyé sous forme de liste : pandas interprète un tuple comme **une** clé
    de colonne, pas comme une sélection multiple.
    """
    return list(config.FEATURE_COLUMNS)


def _clone(estimator: Any) -> Any:
    from sklearn.base import clone

    return clone(estimator)


def _params(spec: models.ModelSpec) -> dict[str, Any]:
    """Hyperparamètres lisibles (sans la tuyauterie de pré-traitement)."""
    inner = spec.estimator
    if hasattr(inner, "regressor"):  # TransformedTargetRegressor
        inner = inner.regressor
    if hasattr(inner, "named_steps"):
        inner = inner.named_steps["modele"]
    raw = inner.get_params(deep=False)
    return {
        key: value
        for key, value in sorted(raw.items())
        if isinstance(value, (int, float, str, bool, type(None)))
    }


def reference_threshold(frame: pd.DataFrame, *, seed: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Recalcule le seuil de la Phase 5 sur la séparation courante.

    Returns:
        `(seuil, baselines_mesurees)` — le seuil contient la borne basse de l'IC
        bootstrap de la meilleure baseline (règle de décision fixée en Phase 5).
    """
    parts = split.split_dataset(frame, seed=seed)
    measured: dict[str, Any] = {}
    for baseline in baselines.build_baselines():
        baseline.fit(parts["train"])
        validation_predictions = baseline.predict(parts["validation"])
        measured[baseline.name] = {
            "definition": baseline.describe()["definition"],
            "metriques": {
                name: evaluation.regression_metrics(
                    parts[name][config.TARGET], baseline.predict(parts[name])
                )
                for name in ("train", "validation", "test")
            },
            "ic_mae_validation": evaluation.bootstrap_mae_ci(
                parts["validation"][config.TARGET], validation_predictions, seed=seed
            ),
        }
    best_name = min(
        measured, key=lambda name: measured[name]["metriques"]["validation"]["mae"]
    )
    interval = measured[best_name]["ic_mae_validation"]
    validation_mae = measured[best_name]["metriques"]["validation"]["mae"]
    threshold = {
        "baseline": best_name,
        "mae_validation": validation_mae,
        "mae_test": measured[best_name]["metriques"]["test"]["mae"],
        "medae_validation": measured[best_name]["metriques"]["validation"]["medae"],
        "mae_borne_basse_ic": interval["mae_borne_basse"],
        "mae_borne_haute_ic": interval["mae_borne_haute"],
        "gain_relatif_a_demontrer_pct": round(
            100.0 * (validation_mae - interval["mae_borne_basse"]) / validation_mae, 2
        ),
    }
    return threshold, measured


def compare_candidates(
    frame: pd.DataFrame,
    *,
    seed: int,
    specs: list[models.ModelSpec] | None = None,
    include_lightgbm: bool = True,
) -> dict[str, Any]:
    """Évalue tous les candidats sur la séparation de référence."""
    parts = split.split_dataset(frame, seed=seed)
    specs = (
        specs
        if specs is not None
        else models.build_models(seed, include_lightgbm=include_lightgbm)
    )
    results: dict[str, Any] = {}
    for spec in specs:
        results[spec.slug] = _fit_evaluate(spec, parts)
    return {"parts": parts, "candidats": results}


def selection_rule(threshold: dict[str, Any]) -> str:
    """Règle de sélection documentée (et reprise telle quelle dans le rapport)."""
    return (
        "Deux étapes : (1) présélection des meilleurs candidats sur la MAE de "
        f"validation de la graine de référence, puis (2) choix, parmi eux, de celui "
        "dont le **gain médian** face à la baseline recalculée sur chaque graine est "
        f"le plus élevé ({len(config.ROBUSTNESS_SEEDS)} graines) ; en cas d'égalité, "
        "la MAE de la graine de référence départage. Le seuil de référence "
        f"({threshold['mae_borne_basse_ic']} FCFA) et la MedAE sont ensuite vérifiés "
        "sur le candidat retenu — ils ne servent pas de critère de tri, la MAE "
        "n'étant pas comparable d'une séparation à l'autre."
    )


def median_gain_pct(block: dict[str, Any]) -> float | None:
    """Gain médian face à la baseline, à travers les graines évaluées.

    Utiliser le gain (et non la MAE brute) neutralise la difficulté propre à
    chaque séparation : la MAE absolue varie du simple au double selon le tirage
    (Phase 5), ce qui rendrait toute comparaison inter-graines trompeuse.
    """
    gains = sorted(run["gain_validation_pct"] for run in block.get("executions", []))
    if not gains:
        return None
    middle = len(gains) // 2
    if len(gains) % 2:
        return float(gains[middle])
    return (gains[middle - 1] + gains[middle]) / 2


def select_best(
    candidates: dict[str, Any],
    threshold: dict[str, Any],
    robustness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Applique la règle de sélection en deux étapes (voir `selection_rule`).

    Sans bloc de robustesse (`robustness=None`), on retombe sur le classement de
    la graine de référence, ce qui sert aux tests unitaires et au mode dégradé.
    """
    ranked = sorted(
        candidates.values(),
        key=lambda item: (item["metriques"]["validation"]["mae"], item["slug"]),
    )
    reference_rank = {item["slug"]: position + 1 for position, item in enumerate(ranked)}

    if robustness:
        scored: list[tuple[float | None, dict[str, Any]]] = []
        for item in ranked:
            block = robustness.get(item["slug"])
            scored.append((median_gain_pct(block) if block else None, item))
        # Les candidats absents de la robustesse (hors présélection) passent en
        # dernier : on ne peut pas confirmer leur gain sur d'autres séparations.
        best = max(
            scored,
            key=lambda pair: (
                pair[0] is not None,
                pair[0] if pair[0] is not None else 0.0,
                -pair[1]["metriques"]["validation"]["mae"],
                pair[1]["slug"],
            ),
        )[1]
    else:
        best = ranked[0]

    best_robustness = (robustness or {}).get(best["slug"], {})
    robust_gain = median_gain_pct(best_robustness) if best_robustness else None
    return {
        "slug": best["slug"],
        "label": best["label"],
        "mae_validation": best["metriques"]["validation"]["mae"],
        "medae_validation": best["metriques"]["validation"]["medae"],
        "mae_test": best["metriques"]["test"]["mae"],
        "medae_test": best["metriques"]["test"]["medae"],
        "seuil_mae_borne_basse_ic": threshold["mae_borne_basse_ic"],
        "rang_graine_reference": reference_rank[best["slug"]],
        "gain_median_pct": robust_gain,
        "bat_le_seuil_validation": best["metriques"]["validation"]["mae"]
        < threshold["mae_borne_basse_ic"],
        "gain_vs_baseline_pct": round(
            100.0
            * (threshold["mae_validation"] - best["metriques"]["validation"]["mae"])
            / threshold["mae_validation"],
            2,
        ),
        "classement": [
            {
                "slug": item["slug"],
                "label": item["label"],
                "famille": item["famille"],
                "cible": item["cible_transformee"],
                "complexite": item["complexite"],
                "interpretabilite": item["interpretabilite"],
                "mae_train": item["metriques"]["train"]["mae"],
                "mae_validation": item["metriques"]["validation"]["mae"],
                "medae_validation": item["metriques"]["validation"]["medae"],
                "mae_test": item["metriques"]["test"]["mae"],
                "medae_test": item["metriques"]["test"]["medae"],
                "r2_validation": item["metriques"]["validation"]["r2"],
                "entrainement_s": item["entrainement_s"],
            }
            for item in ranked
        ],
    }


def shortlist(candidates: dict[str, Any], *, size: int | None = None) -> list[str]:
    """Meilleurs candidats de la graine de référence (à réévaluer sur d'autres)."""
    size = config.SHORTLIST_SIZE if size is None else size
    ordered = sorted(
        candidates.values(),
        key=lambda item: (item["metriques"]["validation"]["mae"], item["slug"]),
    )
    return [item["slug"] for item in ordered[:size]]


def robustness(
    frame: pd.DataFrame,
    *,
    slugs: list[str],
    seeds: tuple[int, ...] | None = None,
    include_lightgbm: bool = True,
) -> dict[str, Any]:
    """Réévalue des candidats sur plusieurs séparations, **face à la baseline**.

    Comparer la MAE d'une graine à celle d'une autre n'a pas de sens : le seuil
    (et donc le gain) doit être recalculé sur **chaque** séparation, sinon on
    compare des découpages et non des modèles. C'est ce que fait cette fonction,
    ce qui permet de compter sur combien de graines le seuil est réellement battu.
    """
    seeds = seeds or config.ROBUSTNESS_SEEDS
    runs: dict[str, list[dict[str, Any]]] = {slug: [] for slug in slugs}
    for seed in seeds:
        threshold, _ = reference_threshold(frame, seed=seed)
        comparison = compare_candidates(
            frame,
            seed=seed,
            specs=[
                spec
                for spec in models.build_models(seed, include_lightgbm=include_lightgbm)
                if spec.slug in slugs
            ],
        )
        baseline_validation = threshold["mae_validation"]
        baseline_test = threshold["mae_test"]
        for slug, result in comparison["candidats"].items():
            validation = result["metriques"]["validation"]
            test = result["metriques"]["test"]
            runs[slug].append(
                {
                    "graine": seed,
                    "mae_validation": validation["mae"],
                    "mae_test": test["mae"],
                    "medae_validation": validation["medae"],
                    "medae_test": test["medae"],
                    "baseline_mae_validation": baseline_validation,
                    "baseline_mae_test": baseline_test,
                    "seuil_borne_basse_ic": threshold["mae_borne_basse_ic"],
                    "gain_validation_pct": round(
                        100.0 * (baseline_validation - validation["mae"]) / baseline_validation, 2
                    ),
                    "gain_test_pct": round(
                        100.0 * (baseline_test - test["mae"]) / baseline_test, 2
                    ),
                    "bat_le_seuil": validation["mae"] < threshold["mae_borne_basse_ic"],
                    "bat_la_baseline": validation["mae"] < baseline_validation,
                }
            )

    summary: dict[str, Any] = {}
    for slug, results in runs.items():
        validation = np.array([run["mae_validation"] for run in results], dtype=float)
        gains = np.array([run["gain_validation_pct"] for run in results], dtype=float)
        gagnants = [run for run in results if run["bat_le_seuil"]]
        baseline_battue = [run for run in results if run["bat_la_baseline"]]
        summary[slug] = {
            "graines": list(seeds),
            "executions": results,
            "mae_validation_moyenne": round(float(validation.mean())),
            "mae_validation_min": int(validation.min()),
            "mae_validation_max": int(validation.max()),
            "gain_validation_moyen_pct": round(float(gains.mean()), 2),
            "gain_validation_median_pct": round(float(np.median(gains)), 2),
            "gain_validation_min_pct": round(float(gains.min()), 2),
            "nb_graines": len(results),
            "nb_graines_battant_le_seuil": len(gagnants),
            "graines_battant_le_seuil": [run["graine"] for run in gagnants],
            "nb_graines_battant_la_baseline": len(baseline_battue),
            "graines_battant_la_baseline": [run["graine"] for run in baseline_battue],
        }
    return summary


def segment_block(
    result: dict[str, Any],
    parts: dict[str, pd.DataFrame],
    *,
    min_n: int,
    split_name: str = "validation",
) -> dict[str, list[dict[str, Any]]]:
    """Performance par segment du modèle retenu (mêmes familles que la Phase 5)."""
    frame = parts[split_name]
    predicted = result["predictions"][split_name]
    truth = frame[config.TARGET]
    neighborhoods = frame["city"].astype(str) + " / " + frame["neighborhood"].astype(str)
    edges = evaluation.price_quartile_edges(parts["train"][config.TARGET])
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


def errors_summary(truth: Any, predicted: Any) -> dict[str, Any]:
    """Résumé des erreurs du modèle retenu, y compris la lecture produit.

    `part_a_moins_de_20_pct` répond à la question « dans quelle proportion la
    prévision tombe-t-elle à ±20 % du loyer observé ? » — plus parlante pour un
    utilisateur que la seule MAE.
    """
    truth_array = np.asarray(truth, dtype=float)
    predicted_array = np.asarray(predicted, dtype=float)
    absolute = np.abs(truth_array - predicted_array)
    relative = absolute / np.maximum(truth_array, 1.0)
    return {
        "n": int(truth_array.size),
        "mae": round(float(mean_absolute_error(truth_array, predicted_array))),
        "rmse": round(float(root_mean_squared_error(truth_array, predicted_array))),
        "r2": round(float(r2_score(truth_array, predicted_array)), 4),
        "medae": round(float(np.median(absolute))),
        "p90": round(float(np.quantile(absolute, 0.9))),
        "part_a_moins_de_20_pct": round(float((relative <= 0.2).mean() * 100), 2),
    }
