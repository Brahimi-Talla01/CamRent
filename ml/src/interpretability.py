"""Explicabilité des prédictions (Phase 6).

Objectif : pouvoir répondre à « pourquoi ce prix ? » sans introduire d'outil
lourd au MVP. Trois niveaux, tous mesurés sur la **validation** (jamais sur le
test, qui reste l'évaluation honnête) :

1. **importance globale** : augmentation de la MAE quand une feature est
   permutée (`permutation_importance`) — effectif et dispersion affichés ;
2. **effet d'une variable** : courbe de dépendance partielle (prédiction moyenne
   lorsque la variable est forcée à chaque valeur observée) ;
3. **explication locale** : pour une annonce donnée, la prévision est replacée
   dans son marché local (médiane ville + quartier + type, avec son effectif),
   ce qui donne un ordre de grandeur compréhensible et vérifiable.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import make_scorer

from . import config


def _inputs(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[list(config.FEATURE_COLUMNS)]


def _neg_median_absolute_error(truth: Any, predicted: Any) -> float:
    """Score d'importance basé sur l'**erreur médiane** (négatif pour sklearn).

    La MAE est dominée par quelques loyers extrêmes conservés : permuter une
    feature utile peut alors *améliorer* la MAE (le modèle produit une valeur
    plus « moyenne », donc plus proche des extrêmes), ce qui donne des
    importances négatives et instables. L'erreur médiane, elle, mesure l'effet
    sur la prévision typique.
    """
    errors = np.abs(np.asarray(truth, dtype=float) - np.asarray(predicted, dtype=float))
    return -float(np.median(errors))


def permutation_importance_table(
    estimator: Any,
    frame: pd.DataFrame,
    *,
    repeats: int | None = None,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """Importance par permutation, en FCFA d'**erreur médiane** supplémentaire.

    Une valeur positive signifie : permuter cette variable dégrade la prévision
    typique (donc le modèle s'appuie dessus). Une valeur proche de zéro indique
    une variable redondante ou peu utilisée.
    """
    repeats = config.PERMUTATION_REPEATS if repeats is None else repeats
    seed = config.RANDOM_SEED if seed is None else seed
    truth = frame[config.TARGET]
    result = permutation_importance(
        estimator,
        _inputs(frame),
        truth,
        scoring=make_scorer(_neg_median_absolute_error),
        n_repeats=repeats,
        random_state=seed,
    )
    rows: list[dict[str, Any]] = []
    for position, column in enumerate(config.FEATURE_COLUMNS):
        # `permutation_importance` renvoie déjà la *baisse de score* : avec un
        # score négatif (‑erreur), c'est l'augmentation de l'erreur — donc ce
        # qu'on veut afficher, sans changement de signe.
        degradation = result.importances[position]
        rows.append(
            {
                "feature": column,
                "n": int(len(frame)),
                "erreur_mediane_supplementaire_moyenne": round(float(degradation.mean())),
                "erreur_mediane_supplementaire_ecart_type": round(float(degradation.std())),
                "erreur_mediane_supplementaire_min": round(float(degradation.min())),
                "erreur_mediane_supplementaire_max": round(float(degradation.max())),
            }
        )
    rows.sort(key=lambda row: row["erreur_mediane_supplementaire_moyenne"], reverse=True)
    return rows


def partial_dependence_table(
    estimator: Any,
    frame: pd.DataFrame,
    feature: str,
) -> list[dict[str, Any]]:
    """Prédiction moyenne lorsque `feature` est forcée à chacune de ses valeurs."""
    if feature not in frame.columns:
        raise ValueError(f"Variable inconnue pour la dépendance partielle : {feature}.")
    values = sorted(pd.unique(frame[feature].dropna()))
    inputs = _inputs(frame)
    rows: list[dict[str, Any]] = []
    for value in values:
        modified = inputs.copy()
        modified[feature] = value
        predictions = np.asarray(estimator.predict(modified), dtype=float)
        is_numeric = isinstance(value, (int, float, np.number))
        rows.append(
            {
                "valeur": float(value) if is_numeric else str(value),
                "n": int(len(modified)),
                "prediction_moyenne": round(float(predictions.mean())),
                "prediction_mediane": round(float(np.median(predictions))),
            }
        )
    return rows


def local_market_context(
    frame_train: pd.DataFrame,
    row: pd.Series,
    *,
    min_n: int | None = None,
) -> dict[str, Any]:
    """Marché local de référence : médiane (ville, quartier, type) et médiane ville.

    Les deux sont calculées sur l'**entraînement** (aucune information de test) et
    toujours accompagnées de leur nombre d'observations (invariant 8).
    """
    min_n = config.MIN_SEGMENT_N if min_n is None else min_n
    same_group = frame_train[
        (frame_train["city"] == row["city"])
        & (frame_train["neighborhood"] == row["neighborhood"])
        & (frame_train["property_type"] == row["property_type"])
    ]
    same_city = frame_train[frame_train["city"] == row["city"]]
    context: dict[str, Any] = {
        "ville": str(row["city"]),
        "quartier": str(row["neighborhood"]),
        "type_de_logement": str(row["property_type"]),
        "n_quartier_type": int(len(same_group)),
        "n_ville": int(len(same_city)),
        "mediane_quartier_type": (
            round(float(same_group[config.TARGET].median())) if len(same_group) else None
        ),
        "mediane_ville": (
            round(float(same_city[config.TARGET].median())) if len(same_city) else None
        ),
        "publiee": bool(len(same_group) >= min_n),
    }
    return context


def explain_prediction(
    estimator: Any,
    row: pd.Series,
    frame_train: pd.DataFrame,
    *,
    interval: tuple[float, float] | None = None,
    min_n: int | None = None,
) -> dict[str, Any]:
    """Explication complète d'une prévision (valeur, fourchette, marché local)."""
    features = _inputs(row.to_frame().T)
    prediction = float(np.asarray(estimator.predict(features), dtype=float)[0])
    context = local_market_context(frame_train, row, min_n=min_n)
    explained: dict[str, Any] = {
        "prevision": round(prediction),
        "loyer_observe": (
            None if pd.isna(row.get(config.TARGET)) else round(float(row[config.TARGET]))
        ),
        "caracteristiques": {
            "ville": str(row["city"]),
            "quartier": str(row["neighborhood"]),
            "type_de_logement": str(row["property_type"]),
            "chambres": None if pd.isna(row["bedrooms"]) else int(row["bedrooms"]),
            "salles_de_bain": None if pd.isna(row["bathrooms"]) else int(row["bathrooms"]),
        },
        "marche_local": context,
    }
    if interval is not None:
        low, high = interval
        explained["intervalle"] = [round(float(low)), round(float(high))]
    if context["mediane_quartier_type"] is not None:
        reference = context["mediane_quartier_type"]
        explained["ecart_vs_mediane_quartier_pct"] = round(
            100.0 * (prediction - reference) / reference, 2
        )
    return explained
