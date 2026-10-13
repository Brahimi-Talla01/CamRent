"""Zoo de modèles (Phase 6) et pipelines d'apprentissage.

Ordre d'exploration imposé par la spec : régression linéaire → Ridge/Lasso →
forêt aléatoire → gradient boosting → LightGBM. Chaque famille est testée sur la
cible brute **et** sur `log1p(cible)` : la distribution des loyers est très
asymétrique (Phase 3), donc l'effet de la transformation doit être mesuré, pas
supposé.

Hyperparamètres : valeurs raisonnables **fixées** (aucune recherche), l'objectif
de la phase étant de comparer des familles, pas d'optimiser. Tous les modèles
partagent le même pré-traitement et la même séparation de données, sans quoi la
comparaison n'aurait pas de sens.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import features

TARGET_TRANSFORMS: tuple[str, ...] = ("brut", "log1p")

# Échelle d'apprentissage de la cible brute : les loyers sont en FCFA (centaines
# de milliers), une régularisation `alpha` y serait négligeable et le Lasso ne
# convergeait pas. On apprend donc en **milliers de FCFA** ; les prévisions et
# toutes les métriques restent converties en FCFA avant évaluation.
TARGET_SCALE: float = 1000.0


def _to_thousands(values: Any) -> Any:
    """Ramène la cible en milliers de FCFA (échelle d'apprentissage)."""
    return np.asarray(values, dtype=float) / TARGET_SCALE


def _from_thousands(values: Any) -> Any:
    """Reconvertit les prévisions en FCFA."""
    return np.asarray(values, dtype=float) * TARGET_SCALE


@dataclass(frozen=True)
class ModelSpec:
    """Un candidat : une famille de modèle et sa transformation de cible."""

    slug: str
    key: str
    label: str
    famille: str
    target_transform: str
    estimator: Any
    complexite: str
    interpretabilite: str


def make_preprocessor() -> ColumnTransformer:
    """Pré-traitement commun : one-hot + imputation médiane (indicateur) + centrage.

    L'imputation est ajustée dans le pipeline, donc **sur l'entraînement
    uniquement** ; `add_indicator` conserve l'information « valeur manquante »
    au lieu de la masquer.
    """
    return ColumnTransformer(
        transformers=[
            (
                "categoriel",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(features.CATEGORICAL_FEATURES),
            ),
            (
                "numerique",
                Pipeline(
                    steps=[
                        ("imputation", SimpleImputer(strategy="median", add_indicator=True)),
                        ("centrage", StandardScaler()),
                    ]
                ),
                list(features.NUMERIC_FEATURES + features.DERIVED_FEATURES),
            ),
        ],
        remainder="drop",
    )


def build_pipeline(estimator: Any, *, target_transform: str) -> Any:
    """Pipeline complet : features → pré-traitement → modèle (+ transformation de cible)."""
    pipeline = Pipeline(
        steps=[
            ("features", features.FeatureBuilder()),
            ("preparation", make_preprocessor()),
            ("modele", estimator),
        ]
    )
    if target_transform == "log1p":
        return TransformedTargetRegressor(
            regressor=pipeline,
            func=np.log1p,
            inverse_func=np.expm1,
        )
    if target_transform != "brut":
        raise ValueError(f"Transformation de cible inconnue : {target_transform}.")
    return TransformedTargetRegressor(
        regressor=pipeline, func=_to_thousands, inverse_func=_from_thousands
    )


def _lightgbm_estimator(seed: int) -> Any | None:
    """LightGBM si la dépendance optionnelle est installée, sinon `None`."""
    try:
        from lightgbm import LGBMRegressor  # import local (dépendance optionnelle)
    except ImportError:
        return None
    return LGBMRegressor(
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        random_state=seed,
        n_jobs=-1,
        verbose=-1,
    )


def _families(seed: int, *, include_lightgbm: bool = True) -> list[dict[str, Any]]:
    """Familles candidates, dans l'ordre d'exploration de la spec."""
    families: list[dict[str, Any]] = [
        {
            "key": "linear",
            "label": "Régression linéaire",
            "famille": "linéaire",
            "estimator": LinearRegression(),
            "complexite": "très faible",
            "interpretabilite": "coefficients directement lisibles",
        },
        {
            "key": "ridge",
            "label": "Ridge",
            "famille": "linéaire régularisé",
            "estimator": Ridge(alpha=1.0),
            "complexite": "très faible",
            "interpretabilite": "coefficients lisibles",
        },
        {
            "key": "lasso",
            "label": "Lasso",
            "famille": "linéaire régularisé",
            "estimator": Lasso(alpha=1.0, max_iter=20_000),
            "complexite": "très faible",
            "interpretabilite": "coefficients lisibles, sélection de variables",
        },
        {
            "key": "random_forest",
            "label": "Forêt aléatoire",
            "famille": "ensemble d'arbres (bagging)",
            "estimator": RandomForestRegressor(
                n_estimators=300, min_samples_leaf=2, random_state=seed, n_jobs=-1
            ),
            "complexite": "moyenne",
            "interpretabilite": "importance par permutation",
        },
        {
            "key": "gradient_boosting",
            "label": "Gradient boosting (scikit-learn)",
            "famille": "ensemble d'arbres (boosting)",
            "estimator": HistGradientBoostingRegressor(
                max_iter=300, learning_rate=0.06, random_state=seed
            ),
            "complexite": "moyenne",
            "interpretabilite": "importance par permutation",
        },
    ]
    if include_lightgbm:
        estimator = _lightgbm_estimator(seed)
        if estimator is not None:
            families.append(
                {
                    "key": "lightgbm",
                    "label": "LightGBM",
                    "famille": "ensemble d'arbres (boosting)",
                    "estimator": estimator,
                    "complexite": "moyenne",
                    "interpretabilite": "importance par permutation",
                }
            )
    return families


def build_models(
    seed: int,
    *,
    include_lightgbm: bool = True,
    target_transforms: tuple[str, ...] = TARGET_TRANSFORMS,
) -> list[ModelSpec]:
    """Construit les candidats (famille × transformation de cible)."""
    specs: list[ModelSpec] = []
    for family in _families(seed, include_lightgbm=include_lightgbm):
        for transform in target_transforms:
            suffix = "" if transform == "brut" else f" ({transform})"
            specs.append(
                ModelSpec(
                    slug=f"{family['key']}_{transform}",
                    key=family["key"],
                    label=f"{family['label']}{suffix}",
                    famille=family["famille"],
                    target_transform=transform,
                    estimator=build_pipeline(family["estimator"], target_transform=transform),
                    complexite=family["complexite"],
                    interpretabilite=family["interpretabilite"],
                )
            )
    return specs


def spec_by_slug(specs: list[ModelSpec], slug: str) -> ModelSpec:
    """Retrouve un candidat par son identifiant (erreur explicite sinon)."""
    for spec in specs:
        if spec.slug == slug:
            return spec
    raise KeyError(f"Candidat inconnu : {slug}.")
