"""Configuration de la Phase 5 (baselines ML).

Module unique de configuration : aucun chemin ni seuil n'est écrit en dur dans
les autres modules. Les valeurs qui dépendent de la machine passent par des
variables d'environnement.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

# Artefacts régénérables (JSON de métriques, ignoré par git) : le livrable
# versionné reste le rapport markdown.
ARTIFACTS_DIR: Final[Path] = Path(
    os.environ.get("CAMRENT_ML_ARTIFACTS", PROJECT_ROOT / "ml" / "artifacts")
)
METRICS_FILENAME: Final[str] = "baseline_metrics.json"
REPORT_PATH: Final[Path] = PROJECT_ROOT / "docs" / "phase-5" / "baseline-report.md"

# Source : mart construit en Phase 4 (`analytics_marts.mart_ml_dataset`).
SOURCE_SCHEMA: Final[str] = os.environ.get("DBT_MARTS_SCHEMA", "analytics_marts")
SOURCE_TABLE: Final[str] = "mart_ml_dataset"
SOURCE_REFERENCE: Final[str] = f"{SOURCE_SCHEMA}.{SOURCE_TABLE}"

# Cible et features du MVP. Les colonnes vides du Silver (`area_m2`,
# `furnished`, `parking`, `gated`) restent exposées par le mart mais ne sont pas
# exploitables : elles ne sont pas listées ici (cf. docs/phase-3).
TARGET: Final[str] = "target_rent_price"
CURRENCY: Final[str] = "XAF"
FEATURE_COLUMNS: Final[tuple[str, ...]] = (
    "city",
    "neighborhood",
    "property_type",
    "bedrooms",
    "bathrooms",
)

# Drapeaux de qualité : exposés, jamais utilisés comme features, uniquement
# pour décrire les scénarios d'évaluation (invariant : aucune exclusion
# silencieuse).
FLAG_COLUMNS: Final[tuple[str, ...]] = (
    "price_is_bound",
    "is_republication",
    "outlier_flags",
    "neighborhood_recognized",
)

REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "listing_key",
    TARGET,
    *FEATURE_COLUMNS,
    *FLAG_COLUMNS,
)

# Séparation des données. Pas de séparation chronologique possible : `posted_at`
# est vide dans le Silver et `collected_at` couvre une seule journée (collecte
# unique), donc aucune information temporelle exploitable (cf. rapport).
SPLIT_SHARES: Final[dict[str, float]] = {
    "train": 0.70,
    "validation": 0.15,
    "test": 0.15,
}
RANDOM_SEED: Final[int] = int(os.environ.get("CAMRENT_ML_SEED", "20261009"))

# Intervalle de confiance de la MAE (bootstrap) : sert à décider si un gain est
# réel ou dans le bruit.
BOOTSTRAP_ITERATIONS: Final[int] = 2000
BOOTSTRAP_ALPHA: Final[float] = 0.05

# Seuil d'observations minimal pour publier une statistique par segment
# (décision Phase 3, reprise telle quelle : invariant 8).
MIN_SEGMENT_N: Final[int] = int(os.environ.get("CAMRENT_MIN_SEGMENT_N", "30"))

# Nombre maximal de quartiers détaillés dans le rapport (tri par volume).
TOP_NEIGHBORHOODS: Final[int] = 10

# --- Phase 6 : modèles ML -------------------------------------------------

# Rapport de la Phase 6 (les artefacts de modèle restent ignorés par git).
MODEL_REPORT_PATH: Final[Path] = PROJECT_ROOT / "docs" / "phase-6" / "model-report.md"
MODELS_DIR: Final[Path] = Path(
    os.environ.get("CAMRENT_MODELS_DIR", PROJECT_ROOT / "ml" / "models")
)
MODEL_ARTIFACT_NAME: Final[str] = "rent_model_v1"

# Fourchette de prédiction : niveau de confiance visé et effectif de validation
# utilisé pour calibrer l'intervalle (split-conformal).
INTERVAL_ALPHA: Final[float] = 0.10

# Robustesse : la MAE de la Phase 5 s'est révélée sensible à l'échantillon, donc
# chaque candidat sérieux est réévalué sur plusieurs séparations (graines).
ROBUSTNESS_SEEDS: Final[tuple[int, ...]] = (20261009, 7, 1234)

# Effectif de la présélection : seuls les meilleurs candidats de la graine de
# référence sont réévalués sur plusieurs graines (coût), puis départagés sur le
# gain **médian** face à la baseline de chaque graine. Sélectionner sur une
# seule séparation reviendrait à choisir du bruit (Phase 5).
SHORTLIST_SIZE: Final[int] = 3

# Explicabilité : permutations par feature et dépendance partielle.
PERMUTATION_REPEATS: Final[int] = 10
PARTIAL_DEPENDENCE_POINTS: Final[int] = 5

# Sauvegarde du modèle retenu (nom de fichier sans extension logique).
MODEL_METADATA_KEYS: Final[tuple[str, ...]] = (
    "nom",
    "famille",
    "cible_transformee",
    "features",
    "hyperparametres",
    "graine",
    "metriques",
    "seuil_phase_5",
    "intervalle",
    "versions",
)
