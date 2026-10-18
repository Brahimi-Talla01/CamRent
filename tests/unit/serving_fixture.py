"""Fixture de modèle isolé pour les tests du serving (ticket #51).

Le bundle est construit **dans le test** : un pipeline scikit-learn minimal
(mêmes classes que la Phase 6) entraîné sur un petit jeu synthétique
déterministe (2 villes, 4 quartiers), plus l'intervalle **quantile** (5 % / 95 %)
calibré sur ce même jeu — la méthode retenue en Phase 6, servie en production.
Aucune dépendance au registre MLflow, aux artefacts du poste local ni à une
base : ces tests doivent passer en CI comme sur une machine neuve (fixture de
serving approfondi : ticket #52).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression

from backend.ml.loader import ServingBundle
from ml.src import models as ml_models
from ml.src import uncertainty

INPUT_COLUMNS: tuple[str, ...] = (
    "city",
    "neighborhood",
    "property_type",
    "bedrooms",
    "bathrooms",
)

# Quartiers volontairement distincts par ville : un quartier connu d'une ville
# mais jamais vu avec l'autre doit être refusé (contrôle du domaine servi).
NEIGHBORHOODS: dict[str, tuple[str, ...]] = {
    "Douala": ("Makepe", "Bonamoussadi"),
    "Yaoundé": ("Bastos", "Mvog-Ada"),
}

MODEL_VERSION = "rent-model-test"
MODEL_URI = "models:/fixture"
# Provenance de test : le serving exige un pin complet (dataset compris), sinon la
# version servie ne serait pas traçable.
DATASET = {
    "source": "analytics_marts.mart_ml_dataset",
    "version": "mart_ml_dataset@fixture",
    "hash_md5": "0" * 32,
    "n_observations": len(NEIGHBORHOODS) * 6,
}


def pin_payload() -> dict[str, object]:
    """Pin complet, au même format que celui écrit par la CLI de promotion (Phase 7)."""
    return {
        "pin_version": 1,
        "nom": "rent-model",
        "version": 1,
        "etiquette": MODEL_VERSION,
        "alias": "champion",
        "run_id": "run-fixture",
        "model_uri": MODEL_URI,
        "dataset": dict(DATASET),
    }


def training_frame() -> pd.DataFrame:
    """Jeu synthétique déterministe : prix linéaires, calculables à la main."""
    rows = []
    for city, neighborhoods in NEIGHBORHOODS.items():
        for position, neighborhood in enumerate(neighborhoods):
            for bedrooms in (1, 2, 3):
                rows.append(
                    {
                        "city": city,
                        "neighborhood": neighborhood,
                        "property_type": "apartment",
                        "bedrooms": bedrooms,
                        "bathrooms": min(bedrooms, 2),
                        "rent": 60_000
                        + position * 30_000
                        + bedrooms * 15_000
                        + (5_000 if city == "Douala" else 0),
                    }
                )
    return pd.DataFrame(rows)


def build_bundle() -> ServingBundle:
    """Pipeline minimal + intervalle **quantile** calibré (méthode retenue en Phase 6)."""
    frame = training_frame()
    model = ml_models.build_pipeline(LinearRegression(), target_transform="log1p")
    model.fit(frame[list(INPUT_COLUMNS)], frame["rent"])
    interval = uncertainty.QuantileRegressionInterval(0.10).fit(
        frame[list(INPUT_COLUMNS)], frame["rent"]
    )
    return ServingBundle(pin=pin_payload(), model=model, interval=interval)


def write_pin(directory: Path) -> Path:
    """Écrit un pin de test dans un répertoire donné (jamais dans le dépôt)."""
    path = directory / "champion.json"
    path.write_text(json.dumps(pin_payload()), encoding="utf-8")
    return path
