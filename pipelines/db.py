"""Chargement du **Silver dataset** dans PostgreSQL (Phase 4 — Data marts).

Lit `data/processed/silver_listings.parquet` (sortie de la Phase 2) et remplit
la table d'atterrissage `landing.silver_listings` dans la base d'exécution
configurée via `DATABASE_URL`.

Idempotent : la table d'atterrissage est **vidée puis remplie** à chaque exécution
(`TRUNCATE` + insertion, par lot). Elle n'est **jamais droppée** : les vues dbt
(staging/intermediate) qui en dépendent survivent au rejeu du chargement, et un
`dbt build` peut être rejoué immédiatement après. La table est une copie dérivée
du Silver Parquet (qui reste la source de vérité du Silver) : aucune donnée brute
ou traitée n'est écrasée. Les modèles dbt construisent ensuite les
faits/dimensions/marts (staging → intermediate → marts).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

from . import config

# Configuration uniquement via variables d'environnement (jamais en dur).
LANDING_SCHEMA: str = os.environ.get("DBT_LANDING_SCHEMA", "landing")
LANDING_TABLE: str = "silver_listings"


def _connection_url(database_url: str | None = None) -> str:
    """Retourne l'URL de connexion (DATABASE_URL, obligatoire)."""
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL n'est pas défini : configurer .env "
            "(voir .env.example) ou passer --database-url."
        )
    return url


def load_silver_to_postgres(
    silver_path: Path | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Charge le Silver Parquet dans `landing.silver_listings` (idempotent).

    La table est vidée (`TRUNCATE`) puis remplie ; elle n'est jamais droppée
    pour ne pas casser les vues dbt qui en dépendent.

    Args:
        silver_path: chemin du Parquet Silver (défaut : config.PROCESSED_ROOT).
        database_url: URL PostgreSQL (défaut : variable DATABASE_URL).

    Returns:
        Dict avec le chemin du Parquet lu, la table cible et le nombre de
        lignes chargées.
    """
    # Validation des entrées AVANT tout import lourd (sqlalchemy) : les
    # messages d'erreur restent clairs même sans l'extra dbt installé.
    _connection_url(database_url)
    path = silver_path or config.PROCESSED_ROOT / config.SILVER_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Silver Parquet introuvable : {path} — lancer d'abord "
            f"`python -m pipelines silver`."
        )

    try:
        df = pd.read_parquet(path)
    except ImportError as exc:  # pyarrow / fastparquet absent
        raise RuntimeError(
            f"Lecture Parquet impossible (moteur manquant) : {exc} — "
            "installer pyarrow ou fastparquet."
        ) from exc
    try:
        from sqlalchemy import create_engine, inspect  # local (extra dbt/transform)
    except ImportError as exc:
        raise RuntimeError(
            "SQLAlchemy est requis pour le chargement en base. Installer : "
            "pip install 'camrent[transform]' (ou SQLAlchemy + psycopg)."
        ) from exc

    url = _connection_url(database_url)
    engine = create_engine(url, future=True)

    schema, table = LANDING_SCHEMA, LANDING_TABLE
    qualified = f"{schema}.{table}"
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        # La table n'est jamais droppée : les vues dbt qui en dépendent
        # survivraient mal à un DROP. On vide puis réinsère.
        exists = inspect(engine).has_table(table, schema=schema)
        if exists:
            with engine.begin() as conn:
                conn.exec_driver_sql(f'TRUNCATE TABLE "{schema}"."{table}"')
        df.to_sql(
            table,
            engine,
            schema=schema,
            if_exists="append" if exists else "fail",
            index=False,
            chunksize=1000,
        )
    finally:
        engine.dispose()

    return {
        "silver_path": str(path),
        "table": qualified,
        "rows": int(len(df)),
    }
