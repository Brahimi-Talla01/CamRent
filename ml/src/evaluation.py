"""Évaluation des baselines : métriques globales, par segment et incertitude.

Métriques retenues (spec Phase 5) : **MAE** (métrique principale, en FCFA),
**RMSE** (pénalise les grosses erreurs) et **R²** (jamais utilisé seul).
Chaque mesure — y compris par segment — porte son **nombre d'observations**
(invariant 8).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

from . import config


def _as_float_arrays(
    y_true: Any, y_pred: Any
) -> tuple[np.ndarray, np.ndarray]:
    truth = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    if truth.shape != predicted.shape:
        raise ValueError(
            f"Tailles incohérentes : y_true={truth.shape} vs y_pred={predicted.shape}."
        )
    if truth.size == 0:
        raise ValueError("Évaluation impossible sur un ensemble vide.")
    if np.isnan(truth).any() or np.isnan(predicted).any():
        raise ValueError("Évaluation impossible : valeurs manquantes dans y_true ou y_pred.")
    return truth, predicted


def regression_metrics(y_true: Any, y_pred: Any) -> dict[str, Any]:
    """MAE, RMSE, R² sur un ensemble, plus deux mesures de robustesse.

    Le R² est `null` avec moins de deux observations (non défini) : il n'est
    jamais présenté comme une mesure de qualité à lui seul. `medae` (erreur
    absolue médiane) et `erreur_absolue_p90` sont fournies en complément : les
    prix étant très asymétriques (quelques valeurs extrêmes conservées), MAE et
    RMSE dépendent fortement de l'échantillon, ce que ces deux mesures
    quantifient sans rien exclure.
    """
    truth, predicted = _as_float_arrays(y_true, y_pred)
    absolute_errors = np.abs(truth - predicted)
    metrics: dict[str, Any] = {
        "n": int(truth.size),
        "mae": round(float(mean_absolute_error(truth, predicted))),
        "rmse": round(float(root_mean_squared_error(truth, predicted))),
        "r2": None if truth.size < 2 else round(float(r2_score(truth, predicted)), 4),
        "medae": round(float(np.median(absolute_errors))),
        "erreur_absolue_p90": round(float(np.quantile(absolute_errors, 0.9))),
        "prix_moyen_observe": round(float(truth.mean())),
    }
    return metrics


def price_quartile_edges(y_train: Any) -> np.ndarray:
    """Bornes des quartiles de prix calculées **sur l'entraînement uniquement**.

    Les bornes servent à segmenter validation et test sans introduire
    d'information issue de ces ensembles.
    """
    truth = np.asarray(y_train, dtype=float)
    if truth.size < 4:
        raise ValueError("Au moins 4 observations d'entraînement sont nécessaires.")
    return np.quantile(truth, [0.0, 0.25, 0.5, 0.75, 1.0])


def price_level_labels(y_true: Any, edges: np.ndarray) -> np.ndarray:
    """Étiquette chaque observation par quartile de prix (`Q1` … `Q4`)."""
    truth = np.asarray(y_true, dtype=float)
    labels = np.array(["Q4"] * truth.size, dtype=object)
    labels[truth <= edges[3]] = "Q3"
    labels[truth <= edges[2]] = "Q2"
    labels[truth <= edges[1]] = "Q1"
    return labels


def bedrooms_labels(values: Any) -> np.ndarray:
    """Regroupe les chambres en segments lisibles (valeurs manquantes isolées)."""
    series = pd.Series(values)
    labels = series.map(
        lambda value: "inconnu" if pd.isna(value) else f"{int(value)} chambre(s)"
    )
    return labels.to_numpy(dtype=object)


def segment_metrics(
    y_true: Any,
    y_pred: Any,
    segments: Any,
    *,
    min_n: int = 0,
    segment_column: str = "segment",
) -> list[dict[str, Any]]:
    """Métriques par segment, triées par volume décroissant.

    Aucun segment n'est masqué : chaque ligne porte son effectif et le drapeau
    `sous_seuil_de_publication` (invariant 8 — un segment sous le seuil n'est pas
    fondu dans un autre, il est étiqueté pour que sa MAE ne soit pas lue comme
    fiable).

    Args:
        y_true/y_pred: valeurs observées et prédites (mêmes longueurs).
        segments: étiquette de segment par observation.
        min_n: seuil en dessous duquel le segment est signalé (décision Phase 3).
        segment_column: nom de la colonne de sortie.
    """
    truth, predicted = _as_float_arrays(y_true, y_pred)
    labels = np.asarray(segments, dtype=object)
    if labels.shape != truth.shape:
        raise ValueError("Les segments doivent avoir la même longueur que les valeurs.")

    frame = pd.DataFrame({segment_column: labels, "y_true": truth, "y_pred": predicted})
    results: list[dict[str, Any]] = []
    for label, group in frame.groupby(segment_column, dropna=False):
        record: dict[str, Any] = {segment_column: str(label)}
        record.update(regression_metrics(group["y_true"], group["y_pred"]))
        record["sous_seuil_de_publication"] = bool(record["n"] < min_n)
        results.append(record)
    results.sort(key=lambda item: (item["n"], item[segment_column]), reverse=True)
    return results


def bootstrap_mae_ci(
    y_true: Any,
    y_pred: Any,
    *,
    iterations: int | None = None,
    alpha: float | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Intervalle de confiance de la MAE par bootstrap (percentiles).

    Sert à distinguer un vrai gain d'une fluctuation d'échantillonnage : une
    amélioration inférieure à la borne basse de cet intervalle n'est pas
    considérée comme démontrée.
    """
    truth, predicted = _as_float_arrays(y_true, y_pred)
    iterations = config.BOOTSTRAP_ITERATIONS if iterations is None else iterations
    alpha = config.BOOTSTRAP_ALPHA if alpha is None else alpha
    if iterations < 1:
        raise ValueError("`iterations` doit être ≥ 1.")
    rng = np.random.default_rng(config.RANDOM_SEED if seed is None else seed)
    errors = np.abs(truth - predicted)
    size = errors.size
    samples = np.empty(iterations, dtype=float)
    for index in range(iterations):
        draw = rng.integers(0, size, size)
        samples[index] = errors[draw].mean()
    low, high = np.quantile(samples, [alpha / 2, 1 - alpha / 2])
    return {
        "n": int(size),
        "iterations": int(iterations),
        "alpha": float(alpha),
        "mae": round(float(errors.mean())),
        "mae_borne_basse": round(float(low)),
        "mae_borne_haute": round(float(high)),
    }
