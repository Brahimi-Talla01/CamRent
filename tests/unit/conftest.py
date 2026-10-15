"""Fixtures partagées des tests unitaires.

Le dataset synthétique de la Phase 5 est construit ici : il reproduit le schéma
de `analytics_marts.mart_ml_dataset` avec des prix choisis pour que les médianes
attendues soient calculables à la main.

La fixture `mlflow_sqlite_uri` (Phase 7) est **de session** : la création des
tables MLflow est coûteuse, on ne la paie donc qu'une fois pour toute la suite.
"""

from __future__ import annotations

import os
import tempfile

# Télémétrie MLflow coupée (vitesse et reproductibilité des tests).
os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")
# Les artefacts des tests ne doivent pas s'écrire dans le dépôt : l'emplacement
# épinglé par défaut est `ml/artifacts/mlflow` (voir ml/src/config.py).
os.environ.setdefault(
    "MLFLOW_ARTIFACT_LOCATION", tempfile.mkdtemp(prefix="camrent-mlflow-artifacts-")
)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(scope="session")
def mlflow_sqlite_uri(tmp_path_factory) -> str:
    """Backend MLflow SQLite partagé par les tests de la Phase 7."""
    directory = tmp_path_factory.mktemp("mlflow")
    return f"sqlite:///{directory / 'mlflow.db'}"


@pytest.fixture
def ml_frame() -> pd.DataFrame:
    """6 observations : 2 villes, 3 quartiers, 2 types, prix connus.

    Médianes attendues :
    - par ville : Douala 200 000 (5 obs), Yaoundé 500 000 (1 obs) ;
    - par (ville, quartier, type) : Bali/appartement 150 000, Makepe/appartement
      350 000, Bastos/appartement 500 000, Bali/studio 50 000.
    """
    rows = [
        ("l1", "Douala", "Bali", "apartment", 2, 2, 100_000, False, False, ""),
        ("l2", "Douala", "Bali", "apartment", 3, 2, 200_000, False, True, ""),
        ("l3", "Douala", "Bali", "studio", 1, 1, 50_000, True, False, ""),
        ("l4", "Douala", "Makepe", "apartment", 2, 2, 300_000, False, False, ""),
        ("l5", "Douala", "Makepe", "apartment", 2, 1, 400_000, False, False, ""),
        ("l6", "Yaoundé", "Bastos", "apartment", 3, 3, 500_000, True, False, "prix_extreme"),
    ]
    frame = pd.DataFrame(
        rows,
        columns=[
            "listing_key",
            "city",
            "neighborhood",
            "property_type",
            "bedrooms",
            "bathrooms",
            "target_rent_price",
            "price_is_bound",
            "is_republication",
            "outlier_flags",
        ],
    )
    frame["neighborhood_recognized"] = frame["neighborhood"].isin(
        ["Bali", "Makepe", "Bastos"]
    )
    frame["collected_at"] = "2026-10-09T07:05:36+00:00"
    frame["posted_at"] = None
    return frame


@pytest.fixture
def ml_dataset() -> pd.DataFrame:
    """Dataset synthétique déterministe (300 lignes) pour l'entraînement.

    Le prix est construit comme une fonction monotone de la ville, du quartier,
    du type, des chambres et des salles de bain (plus un bruit faible) : un
    modèle correct doit donc pouvoir battre la moyenne globale, et les tests
    d'importance de variables doivent retrouver les bons facteurs.
    """
    rng = np.random.default_rng(20261009)
    size = 300
    cities = rng.choice(["Douala", "Yaoundé"], size=size, p=[0.8, 0.2])
    neighborhoods_by_city = {
        "Douala": ["Makepe", "Bonamoussadi", "Akwa"],
        "Yaoundé": ["Bastos", "Odza"],
    }
    neighborhoods = np.array(
        [rng.choice(neighborhoods_by_city[city]) for city in cities], dtype=object
    )
    property_types = rng.choice(["apartment", "studio"], size=size, p=[0.75, 0.25])
    bedrooms = rng.integers(1, 5, size=size)
    bathrooms = rng.integers(1, 4, size=size)
    neighborhood_bonus = np.where(
        np.isin(neighborhoods, ["Bonamoussadi", "Bastos"]), 40_000, 0
    )
    base = (
        np.where(cities == "Douala", 60_000, 90_000)
        + neighborhood_bonus
        + bedrooms * 25_000
        + bathrooms * 8_000
        + np.where(property_types == "studio", -20_000, 0)
    )
    price = np.clip((base * rng.normal(1.0, 0.05, size=size)).round(-3), 1, None)

    frame = pd.DataFrame(
        {
            "listing_key": [f"s{index:04d}" for index in range(size)],
            "city": cities,
            "neighborhood": neighborhoods,
            "property_type": property_types,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "target_rent_price": price,
            "price_is_bound": rng.random(size) < 0.2,
            "is_republication": rng.random(size) < 0.1,
            "outlier_flags": "",
            "neighborhood_recognized": True,
            "collected_at": "2026-10-09T07:05:36+00:00",
            "posted_at": None,
        }
    )
    return frame
