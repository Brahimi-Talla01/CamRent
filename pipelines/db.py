"""Chargement des données de la Data Platform dans PostgreSQL.

Trois tables d'atterrissage (schéma `landing`), toutes rejouables à l'identique :

- `silver_listings`   ← `data/processed/silver_listings.parquet` (Phase 2) ;
- `quarantine_listings` ← `data/processed/quarantine_listings.parquet` (rejets) ;
- `ingestion_runs`    ← `data/raw/metadata/<date>/*.json` (un lot par fichier).

Les deux dernières (lot B, plan de réalignement §7.6) rendent les **rejets** et la
**provenance des lots** interrogeables en base : matière première du module
« Qualité » du back-office et de la Phase 11.

Idempotence : chaque table est **vidée puis remplie** (`TRUNCATE` + insertion, par
lot). Aucune table n'est **jamais droppée** : les vues dbt qui en dépendent
survivent au rejeu du chargement, et un `dbt build` peut être rejoué immédiatement
après. Ces tables sont des copies dérivées des artefacts de la Data Platform
(Parquet et métadonnées, qui restent les sources de vérité) : aucune donnée brute
ou traitée n'est écrasée.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from . import config

# Configuration uniquement via variables d'environnement (jamais en dur).
LANDING_SCHEMA: str = os.environ.get("DBT_LANDING_SCHEMA", "landing")
LANDING_TABLE: str = "silver_listings"
QUARANTINE_TABLE: str = "quarantine_listings"
INGESTION_RUNS_TABLE: str = "ingestion_runs"

# Colonnes des lots d'ingestion exposées en base (ordre stable, une ligne par lot).
INGESTION_RUN_COLUMNS: tuple[str, ...] = (
    "source",
    "category",
    "method",
    "format",
    "collected_day",
    "collected_at",
    "record_count",
    "raw_file",
    "rights_status",
    "n_urls",
    "connector_version",
    "content_bytes",
    "content_sha256",
    "lot_validation_status",
    "lot_validation_failures",
    "notes",
)

# Colonnes numériques des lots : typées explicitement pour que la présence de
# valeurs manquantes (lots antérieurs à la provenance renforcée) ne fasse pas
# déduire un type au hasard.
INGESTION_RUN_NUMERIC_COLUMNS: tuple[str, ...] = (
    "record_count",
    "n_urls",
    "content_bytes",
)


def _connection_url(database_url: str | None = None) -> str:
    """Retourne l'URL de connexion (DATABASE_URL, obligatoire)."""
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL n'est pas défini : configurer .env "
            "(voir .env.example) ou passer --database-url."
        )
    return url


def _read_parquet(path: Path, hint: str) -> pd.DataFrame:
    """Lit un Parquet de la Data Platform, avec des erreurs explicites."""
    if not path.exists():
        raise FileNotFoundError(f"Parquet introuvable : {path} — {hint}")
    try:
        return pd.read_parquet(path)
    except ImportError as exc:  # pyarrow / fastparquet absent
        raise RuntimeError(
            f"Lecture Parquet impossible (moteur manquant) : {exc} — "
            "installer pyarrow ou fastparquet."
        ) from exc


def _load_dataframe(engine: Any, table: str, frame: pd.DataFrame) -> str:
    """Charge un DataFrame dans `<landing>.<table>` (vidage puis insertion).

    La table n'est jamais droppée : on vide (`TRUNCATE`) si elle existe, puis on
    insère. Retourne le nom qualifié de la table.
    """
    schema = LANDING_SCHEMA
    qualified = f"{schema}.{table}"
    with engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    from sqlalchemy import inspect  # local (extra dbt/transform)  # noqa: PLC0415

    exists = inspect(engine).has_table(table, schema=schema)
    if exists:
        with engine.begin() as conn:
            conn.exec_driver_sql(f'TRUNCATE TABLE "{schema}"."{table}"')
    frame.to_sql(
        table,
        engine,
        schema=schema,
        if_exists="append" if exists else "fail",
        index=False,
        chunksize=1000,
    )
    return qualified


def _connect(database_url: str | None) -> Any:
    """Valide l'URL puis crée l'Engine SQLAlchemy (import local, erreur claire)."""
    url = _connection_url(database_url)
    try:
        from sqlalchemy import create_engine  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "SQLAlchemy est requis pour le chargement en base. Installer : "
            "pip install 'camrent[transform]' (ou SQLAlchemy + psycopg)."
        ) from exc
    return create_engine(url, future=True)


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
    df = _read_parquet(
        path, "lancer d'abord `python -m pipelines silver`."
    )
    engine = _connect(database_url)
    try:
        qualified = _load_dataframe(engine, LANDING_TABLE, df)
    finally:
        engine.dispose()

    return {
        "silver_path": str(path),
        "table": qualified,
        "rows": int(len(df)),
    }


def load_quarantine_to_postgres(
    quarantine_path: Path | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Charge la quarantaine de la Phase 2 dans `landing.quarantine_listings`.

    Une ligne par observation **rejetée**, avec son motif (`quarantine_reason`) :
    les rejets sont conservés, jamais supprimés ni masqués. Même stratégie
    idempotente que le Silver (vidage puis insertion, aucun `DROP`).

    Returns:
        Dict avec le chemin du Parquet lu, la table cible, le nombre de lignes
        chargées et la répartition par motif.
    """
    _connection_url(database_url)
    path = quarantine_path or config.PROCESSED_ROOT / config.QUARANTINE_FILENAME
    df = _read_parquet(
        path, "lancer d'abord `python -m pipelines silver`."
    )
    engine = _connect(database_url)
    try:
        qualified = _load_dataframe(engine, QUARANTINE_TABLE, df)
    finally:
        engine.dispose()

    by_reason: dict[str, int] = {}
    if "quarantine_reason" in df.columns:
        by_reason = {
            str(reason): int(count)
            for reason, count in df["quarantine_reason"].value_counts().items()
        }
    return {
        "quarantine_path": str(path),
        "table": qualified,
        "rows": int(len(df)),
        "by_reason": by_reason,
    }


def read_ingestion_runs(raw_root: Path | None = None) -> list[dict[str, Any]]:
    """Lit les métadonnées de lot de `data/raw/metadata/<date>/*.json`.

    Retourne une ligne par lot, dans l'ordre chronologique des chemins. Un lot
    dont les métadonnées sont illisibles est conservé avec
    `lot_validation_status = "unreadable"` : aucune donnée n'est écartée
    silencieusement (invariant 5).

    Les lots antérieurs à la provenance renforcée n'ont ni version de connecteur
    ni empreinte : les colonnes correspondantes restent nulles plutôt que
    d'inventer une valeur.
    """
    root = (raw_root or config.RAW_ROOT) / "metadata"
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*.json")):
        rel = path.relative_to(raw_root or config.RAW_ROOT)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            rows.append(
                {
                    "source": None,
                    "category": None,
                    "method": None,
                    "format": None,
                    "collected_day": path.parent.name,
                    "collected_at": None,
                    "record_count": None,
                    "raw_file": str(rel),
                    "rights_status": None,
                    "n_urls": None,
                    "connector_version": None,
                    "content_bytes": None,
                    "content_sha256": None,
                    "lot_validation_status": "unreadable",
                    "lot_validation_failures": [],
                    "notes": "",
                }
            )
            continue
        urls = payload.get("urls") or []
        failures = payload.get("lot_validation_failures") or []
        rows.append(
            {
                "source": payload.get("source"),
                "category": payload.get("category"),
                "method": payload.get("method"),
                "format": payload.get("format"),
                "collected_day": payload.get("collected_day") or path.parent.name,
                "collected_at": payload.get("collected_at"),
                "record_count": payload.get("record_count"),
                "raw_file": payload.get("raw_file") or str(rel),
                "rights_status": payload.get("rights_status"),
                "n_urls": len(urls),
                "connector_version": payload.get("connector_version"),
                "content_bytes": payload.get("content_bytes"),
                "content_sha256": payload.get("content_sha256"),
                "lot_validation_status": payload.get("lot_validation_status"),
                "lot_validation_failures": "; ".join(str(f) for f in failures),
                "notes": payload.get("notes", ""),
            }
        )
    return rows


def load_ingestion_runs_to_postgres(
    database_url: str | None = None,
    raw_root: Path | None = None,
) -> dict[str, Any]:
    """Charge les métadonnées de lot dans `landing.ingestion_runs`.

    Une ligne par lot de collecte : source, jour, volume déclaré, fichier brut,
    droits, et — depuis la provenance renforcée — version du connecteur,
    empreinte de contenu et statut de validation.
    """
    _connection_url(database_url)
    rows = read_ingestion_runs(raw_root)
    frame = pd.DataFrame(rows, columns=list(INGESTION_RUN_COLUMNS))
    for column in INGESTION_RUN_NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    engine = _connect(database_url)
    try:
        qualified = _load_dataframe(engine, INGESTION_RUNS_TABLE, frame)
    finally:
        engine.dispose()

    return {
        "raw_root": str(raw_root or config.RAW_ROOT),
        "table": qualified,
        "rows": int(len(frame)),
        "sources": sorted({str(row["source"]) for row in rows if row["source"]}),
    }


def load_all_to_postgres(
    silver_path: Path | None = None,
    quarantine_path: Path | None = None,
    database_url: str | None = None,
    raw_root: Path | None = None,
) -> dict[str, Any]:
    """Charge les trois tables d'atterrissage de la Data Platform.

    Returns:
        Un dict avec une entrée par table chargée (`silver`, `quarantine`,
        `ingestion_runs`).
    """
    return {
        "silver": load_silver_to_postgres(
            silver_path=silver_path, database_url=database_url
        ),
        "quarantine": load_quarantine_to_postgres(
            quarantine_path=quarantine_path, database_url=database_url
        ),
        "ingestion_runs": load_ingestion_runs_to_postgres(
            database_url=database_url, raw_root=raw_root
        ),
    }
