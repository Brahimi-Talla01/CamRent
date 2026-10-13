"""Chargement et qualification du dataset ML (Phase 4 → Phase 5).

Fonctions pures et testables sans base : `load_ml_dataset` est la seule fonction
qui touche PostgreSQL, et l'accès se fait par injection d'`engine` pour rester
vérifiable sans base.
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from . import config

# Scénarios d'évaluation. Aucun n'est présenté comme « le » dataset : le
# scénario principal conserve toutes les observations (invariant : aucune
# exclusion silencieuse) et les autres sont des analyses de sensibilité
# explicitement étiquetées.
SCENARIOS: dict[str, str] = {
    "toutes_observations": (
        "Toutes les observations du mart (aucune exclusion) — scénario principal."
    ),
    "hors_republications": (
        "Observations hors républications (`is_republication = false`) : réduit le "
        "risque d'annonces quasi identiques entre entraînement et test."
    ),
    "prix_exacts_sans_aberration": (
        "Observations à prix exact (`price_is_bound = false`) et sans aberration "
        "(`outlier_flags` vide) : cible la plus fiable, mais volumes faibles."
    ),
}
PRIMARY_SCENARIO = "toutes_observations"


def load_ml_dataset(
    database_url: str | None = None,
    *,
    engine: Any | None = None,
) -> pd.DataFrame:
    """Charge `analytics_marts.mart_ml_dataset` dans un DataFrame.

    Args:
        database_url: URL PostgreSQL (défaut : variable d'environnement
            `DATABASE_URL`).
        engine: moteur SQLAlchemy déjà construit (injection pour les tests).

    Returns:
        Le dataset ML tel quel (aucune ligne filtrée, aucune valeur imputée).

    Raises:
        RuntimeError: `DATABASE_URL` absente ou dépendances SQL manquantes.
        ValueError: colonnes attendues absentes du mart.
    """
    if engine is None:
        url = database_url or os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "DATABASE_URL (ou --database-url) est requis pour lire "
                f"{config.SOURCE_REFERENCE}."
            )
        try:
            from sqlalchemy import create_engine  # import local (dépendance lourde)
        except ImportError as exc:  # pragma: no cover - dépend de l'environnement
            raise RuntimeError(
                "SQLAlchemy est requis pour lire le mart. Installer : "
                "pip install 'camrent[transform]' (ou SQLAlchemy + psycopg)."
            ) from exc
        engine = create_engine(url, future=True)

    query = f'select * from "{config.SOURCE_SCHEMA}"."{config.SOURCE_TABLE}"'
    frame = pd.read_sql(query, engine)
    validate_columns(frame)
    return frame


def validate_columns(frame: pd.DataFrame) -> None:
    """Valide les colonnes attendues à la frontière (aucune transformation)."""
    missing = [column for column in config.REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(
            f"Colonnes manquantes dans {config.SOURCE_REFERENCE} : {', '.join(missing)}."
        )


def _outlier_flags(frame: pd.DataFrame) -> pd.Series:
    """`outlier_flags` est une chaîne vide (pas un NaN) pour les non-aberrations."""
    return frame["outlier_flags"].fillna("").astype(str).str.strip()


def scenario_frames(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Découpe le dataset en scénarios d'évaluation (mêmes colonnes, sous-ensembles)."""
    masks: dict[str, pd.Series] = {
        "toutes_observations": pd.Series(True, index=frame.index),
        "hors_republications": ~frame["is_republication"].astype(bool),
        "prix_exacts_sans_aberration": (~frame["price_is_bound"].astype(bool))
        & (_outlier_flags(frame) == ""),
    }
    order = [name for name in SCENARIOS if name in masks]
    return {name: frame.loc[masks[name]].reset_index(drop=True) for name in order}


def describe_quality(frame: pd.DataFrame) -> dict[str, Any]:
    """Compte les marqueurs de qualité (pour le rapport, jamais pour filtrer)."""
    flags = _outlier_flags(frame)
    return {
        "n_observations": int(len(frame)),
        "prix_borne": int(frame["price_is_bound"].astype(bool).sum()),
        "republications": int(frame["is_republication"].astype(bool).sum()),
        "aberrations": int((flags != "").sum()),
        "quartiers_non_reconnus": int((~frame["neighborhood_recognized"].astype(bool)).sum()),
        "chambres_manquantes": int(frame["bedrooms"].isna().sum()),
        "salles_de_bain_manquantes": int(frame["bathrooms"].isna().sum()),
        "villes": sorted(frame["city"].dropna().unique().tolist()),
        "quartiers": int(frame["neighborhood"].nunique()),
        "paires_ville_quartier_type": int(
            frame[["city", "neighborhood", "property_type"]].drop_duplicates().shape[0]
        ),
    }


def describe_chronology(frame: pd.DataFrame) -> dict[str, Any]:
    """Décrit l'information temporelle disponible (justifie la séparation aléatoire)."""
    collected = pd.to_datetime(frame["collected_at"], errors="coerce", utc=True)
    result: dict[str, Any] = {
        "collected_at_min": None if collected.isna().all() else collected.min().isoformat(),
        "collected_at_max": None if collected.isna().all() else collected.max().isoformat(),
        "jours_de_collecte_distincts": int(collected.dt.date.nunique()),
    }
    if "posted_at" in frame.columns:
        posted = pd.to_datetime(frame["posted_at"], errors="coerce", utc=True)
        result["posted_at_renseignes"] = int(posted.notna().sum())
    return result
