"""Intervalles de prédiction (Phase 6).

Deux méthodes candidates, comparées puis validées expérimentalement — aucune
fourchette n'est publiée sans mesure de sa **couverture** :

1. **split-conformal** (méthode de référence) : le quantile `1 - alpha` des
   erreurs absolues observées en **validation** définit une demi-largeur, ensuite
   appliquée telle quelle aux nouvelles prévisions. Hypothèse minimale
   (échangeabilité), calibrée sans toucher au test.
2. **régression quantile** : deux modèles de gradient boosting entraînés sur
   l'entraînement pour les quantiles `alpha/2` et `1 - alpha/2`.

La méthode retenue est celle dont la couverture de validation est la plus proche
du niveau visé, à largeur comparable ; la couverture de **test** est ensuite
mesurée pour vérifier que le choix tient sur des données jamais vues.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from . import config, models

METHOD_LABELS = {
    "split_conformal": "Split-conformal (quantile des erreurs absolues de validation)",
    "quantile_regression": "Régression quantile (gradient boosting)",
}

# Un loyer ne peut pas être négatif : la borne basse est plancherée (invariant
# produit — jamais afficher une fourchette impossible).
MIN_RENT: float = 1.0


def _clamp_lower(values: np.ndarray) -> np.ndarray:
    """Ramène la borne basse au minimum physique d'un loyer."""
    return np.maximum(np.asarray(values, dtype=float), MIN_RENT)


def coverage_report(truth: Any, lower: Any, upper: Any) -> dict[str, Any]:
    """Couverture empirique, largeur et effectif d'un intervalle."""
    y = np.asarray(truth, dtype=float)
    low = np.asarray(lower, dtype=float)
    high = np.asarray(upper, dtype=float)
    if not (y.shape == low.shape == high.shape):
        raise ValueError("Couverture impossible : tailles incohérentes.")
    if y.size == 0:
        raise ValueError("Couverture impossible sur un ensemble vide.")
    if np.any(high < low):
        raise ValueError("Intervalle invalide : borne haute inférieure à la borne basse.")
    widths = high - low
    return {
        "n": int(y.size),
        "couverture_pct": round(float(((y >= low) & (y <= high)).mean() * 100), 2),
        "largeur_moyenne": round(float(widths.mean())),
        "largeur_mediane": round(float(np.median(widths))),
    }


class ConformalInterval:
    """Split-conformal symétrique, calibré sur la validation."""

    method = "split_conformal"

    def __init__(self, alpha: float | None = None) -> None:
        self.alpha = config.INTERVAL_ALPHA if alpha is None else alpha
        self.demi_largeur: float | None = None

    def fit(self, truth: Any, predictions: Any) -> ConformalInterval:
        residuals = np.abs(np.asarray(truth, dtype=float) - np.asarray(predictions, dtype=float))
        if residuals.size == 0:
            raise ValueError("Calibration impossible sans résidus de validation.")
        self.demi_largeur = float(np.quantile(residuals, 1 - self.alpha))
        return self

    def bounds(self, predictions: Any) -> tuple[np.ndarray, np.ndarray]:
        if self.demi_largeur is None:
            raise RuntimeError("Intervalle non calibré (`fit` requis avant `bounds`).")
        values = np.asarray(predictions, dtype=float)
        return _clamp_lower(values - self.demi_largeur), values + self.demi_largeur

    def describe(self) -> dict[str, Any]:
        return {
            "methode": self.method,
            "libelle": METHOD_LABELS[self.method],
            "alpha": self.alpha,
            "demi_largeur_fcfa": None if self.demi_largeur is None else round(self.demi_largeur),
        }


class QuantileRegressionInterval:
    """Deux modèles de gradient boosting pour les quantiles bas et haut."""

    method = "quantile_regression"

    def __init__(self, alpha: float | None = None, *, seed: int | None = None) -> None:
        self.alpha = config.INTERVAL_ALPHA if alpha is None else alpha
        self.seed = config.RANDOM_SEED if seed is None else seed
        self._lower: Any | None = None
        self._upper: Any | None = None

    def _estimator(self, quantile: float) -> Any:
        return models.build_pipeline(
            HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                max_iter=300,
                learning_rate=0.06,
                random_state=self.seed,
            ),
            target_transform="brut",
        )

    def fit(self, frame: pd.DataFrame, truth: Any) -> QuantileRegressionInterval:
        self._lower = self._estimator(self.alpha / 2).fit(frame, truth)
        self._upper = self._estimator(1 - self.alpha / 2).fit(frame, truth)
        return self

    def bounds(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        if self._lower is None or self._upper is None:
            raise RuntimeError("Intervalle non entraîné (`fit` requis avant `bounds`).")
        low = np.asarray(self._lower.predict(frame), dtype=float)
        high = np.asarray(self._upper.predict(frame), dtype=float)
        return _clamp_lower(np.minimum(low, high)), np.maximum(low, high)

    def describe(self) -> dict[str, Any]:
        return {
            "methode": self.method,
            "libelle": METHOD_LABELS[self.method],
            "alpha": self.alpha,
            "quantiles": [self.alpha / 2, 1 - self.alpha / 2],
        }


def choose_method(results: dict[str, Any], *, alpha: float) -> tuple[str, str]:
    """Choisit la méthode : couverture suffisante d'abord, puis fourchette la plus étroite.

    Ordre de décision : (1) la méthode doit couvrir au moins le niveau visé, à la
    tolérance près, sur la validation ; (2) parmi celles qui couvrent, la plus
    étroite gagne — sur la **largeur médiane**, une moyenne étant tirée par
    quelques cas très incertains ; (3) sinon, la couverture la plus proche du
    niveau visé.
    """
    nominal = (1 - alpha) * 100
    tolerance = 2.0

    def covers(name: str) -> bool:
        return results[name]["validation"]["couverture_pct"] >= nominal - tolerance

    covering = [name for name in results if covers(name)]
    if covering:
        retained = min(
            covering, key=lambda name: results[name]["validation"]["largeur_mediane"]
        )
    else:
        retained = min(
            results,
            key=lambda name: abs(results[name]["validation"]["couverture_pct"] - nominal),
        )
    rationale = (
        f"Parmi les méthodes couvrant au moins le niveau visé ({nominal:.0f} % de "
        "validation), la fourchette la plus étroite (largeur médiane) est retenue ; la "
        "couverture de test sert de vérification, jamais de réglage."
        if covering
        else f"Aucune méthode n'atteint {nominal:.0f} % en validation : la plus proche est retenue."
    )
    return retained, rationale


def _inputs(frame: pd.DataFrame) -> pd.DataFrame:
    """Colonnes d'entrée du mart (le pipeline construit lui-même les features)."""
    return frame[list(config.FEATURE_COLUMNS)]


def compare_methods(
    parts: dict[str, pd.DataFrame],
    *,
    predictions: dict[str, np.ndarray],
    alpha: float | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Calibre et compare les deux méthodes sur le modèle retenu.

    Args:
        parts: ensembles `train` / `validation` / `test`.
        predictions: prévisions du modèle retenu, par ensemble.
        alpha: risque (défaut : `config.INTERVAL_ALPHA`, soit 90 % de couverture).
        seed: graine des modèles de régression quantile.
    """
    alpha = config.INTERVAL_ALPHA if alpha is None else alpha
    seed = config.RANDOM_SEED if seed is None else seed

    results: dict[str, Any] = {}

    conformal = ConformalInterval(alpha).fit(
        parts["validation"][config.TARGET], predictions["validation"]
    )
    results[conformal.method] = {"description": conformal.describe()}
    for split_name in ("validation", "test"):
        low, high = conformal.bounds(predictions[split_name])
        results[conformal.method][split_name] = coverage_report(
            parts[split_name][config.TARGET], low, high
        )

    quantile = QuantileRegressionInterval(alpha, seed=seed).fit(
        _inputs(parts["train"]), parts["train"][config.TARGET]
    )
    results[quantile.method] = {"description": quantile.describe()}
    for split_name in ("validation", "test"):
        low, high = quantile.bounds(_inputs(parts[split_name]))
        results[quantile.method][split_name] = coverage_report(
            parts[split_name][config.TARGET], low, high
        )

    retained, rationale = choose_method(results, alpha=alpha)
    return {
        "alpha": alpha,
        "niveau_vise_pct": round((1 - alpha) * 100),
        "methodes": results,
        "methode_retenue": retained,
        "justification": rationale,
    }


def retained_interval(
    method: str,
    parts: dict[str, pd.DataFrame],
    *,
    predictions: dict[str, np.ndarray],
    alpha: float | None = None,
    seed: int | None = None,
) -> ConformalInterval | QuantileRegressionInterval:
    """Reconstruit l'intervalle retenu, calibré exactement comme lors de la comparaison.

    Sert à expliquer une prévision précise (explication locale du rapport) avec
    la même méthode que celle retenue pour le produit.
    """
    alpha = config.INTERVAL_ALPHA if alpha is None else alpha
    seed = config.RANDOM_SEED if seed is None else seed
    if method == ConformalInterval.method:
        return ConformalInterval(alpha).fit(
            parts["validation"][config.TARGET], predictions["validation"]
        )
    if method == QuantileRegressionInterval.method:
        return QuantileRegressionInterval(alpha, seed=seed).fit(
            _inputs(parts["train"]), parts["train"][config.TARGET]
        )
    raise ValueError(f"Méthode d'intervalle inconnue : {method}.")
