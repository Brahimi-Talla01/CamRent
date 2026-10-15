"""Suivi des expériences MLflow (Phase 7).

Responsabilité unique : **journaliser** les runs. Chaque candidat de la Phase 6
(12 modèles) devient un run de l'expérience `rent_prediction`, avec les
paramètres, les métriques des trois ensembles, la version du dataset et la
version du code — de sorte qu'aucun modèle ne soit retenu « sur une impression ».

L'URI de suivi n'est jamais écrite en dur : `MLFLOW_TRACKING_URI` si fourni,
sinon une base PostgreSQL dédiée dérivée de `DATABASE_URL`, sinon un backend
fichiers local (rejeu hors-ligne et tests). Le nom de la base PostgreSQL est
`mlflow` par défaut, pour ne pas mélanger les tables du registre avec celles de
l'application.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any

import mlflow
import pandas as pd

from . import config, persistence

# Métriques numériques journalisées pour chaque ensemble d'évaluation.
_METRIC_SUFFIXES: tuple[str, ...] = (
    "n",
    "mae",
    "rmse",
    "r2",
    "medae",
    "erreur_absolue_p90",
    "prix_moyen_observe",
    "temps_prediction_s",
)
_SPLITS: tuple[str, ...] = ("train", "validation", "test")


def _from_database_url(database_url: str | None = None) -> str | None:
    """Dérive une base PostgreSQL dédiée (`mlflow`) depuis `DATABASE_URL`."""
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        from sqlalchemy.engine import make_url  # import local (dépendance lourde)
    except ImportError:  # pragma: no cover - dépend de l'environnement
        return None
    try:
        parsed = make_url(url)
    except Exception:  # pragma: no cover - URL invalide fournie par l'utilisateur
        return None
    if not parsed.drivername.startswith("postgresql"):
        # Base non PostgreSQL (ex. SQLite) : la dérivation n'a pas de sens pour le
        # registre, on préfère le backend local fichiers.
        return None
    # `str(URL)` masque le mot de passe en `***` : il faut rendre la chaîne réelle.
    return parsed.set(
        drivername="postgresql+psycopg", database=config.MLFLOW_DATABASE_NAME
    ).render_as_string(hide_password=False)


def resolve_tracking_uri(explicit: str | None = None, database_url: str | None = None) -> str:
    """URI de suivi effectivement utilisée (aucun secret en dur)."""
    if explicit:
        return explicit
    if config.MLFLOW_TRACKING_URI:
        return config.MLFLOW_TRACKING_URI
    derived = _from_database_url(database_url)
    if derived:
        return derived
    return str(config.MLFLOW_LOCAL_DIR)


def configure(explicit: str | None = None, database_url: str | None = None) -> str:
    """Pointe MLflow vers l'URI résolue et renvoie celle-ci."""
    uri = resolve_tracking_uri(explicit, database_url)
    mlflow.set_tracking_uri(uri)
    return uri


def mask_tracking_uri(uri: str) -> str:
    """URI de suivi sans mot de passe, pour tout affichage ou rapport versionné."""
    try:
        from sqlalchemy.engine import make_url  # import local (dépendance lourde)
    except ImportError:  # pragma: no cover - dépend de l'environnement
        return uri
    try:
        return make_url(uri).render_as_string(hide_password=True)
    except Exception:  # pragma: no cover - URI non SQLAlchemy (file store, etc.)
        return uri


def ensure_experiment(name: str | None = None, *, artifact_location: str | None = None) -> str:
    """Crée l'expérience si besoin et renvoie son identifiant."""
    name = name or config.MLFLOW_EXPERIMENT
    client = mlflow.MlflowClient()
    existing = client.get_experiment_by_name(name)
    if existing is not None:
        # `get_experiment_by_name` renvoie aussi les expériences supprimées : les
        # restaurer évite l'erreur « must be in the 'active' state » au prochain run.
        if existing.lifecycle_stage != "active":
            client.restore_experiment(existing.experiment_id)
        return existing.experiment_id
    location = artifact_location or config.MLFLOW_ARTIFACT_LOCATION
    return client.create_experiment(name, artifact_location=location)


def _git(args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=config.PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def code_version() -> dict[str, Any]:
    """Version du code (Git) et versions logicielles, pour la reproductibilité."""
    dirty = _git(["status", "--porcelain"])
    return {
        "git_sha": _git(["rev-parse", "HEAD"]),
        "git_branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_dirty": None if dirty is None else bool(dirty),
        "logiciel": persistence.versions(),
    }


def dataset_version(frame: pd.DataFrame) -> dict[str, Any]:
    """Identifiant de version du dataset : source, volume et hash du contenu.

    Le hash couvre **tout le contenu du mart** : les noms de colonnes (donc le
    schéma) et toutes les valeurs, ligne par ligne. Ajouter, retirer ou modifier une
    colonne — y compris une feature — produit donc une nouvelle version. Sans cela,
    un run pourrait porter une version identique alors que ses données d'entrée ont
    changé, ce qui donnerait une fausse garantie de reproductibilité.

    DVC / lakeFS ne sont pas introduits : les volumes du MVP (quelques milliers de
    lignes) ne les justifient pas ; un hash documenté suffit à savoir sur quelle
    version de données un modèle a été entraîné.
    """
    columns = sorted(str(column) for column in frame.columns)
    ordered = frame.sort_values("listing_key")[columns]
    # Conversion explicite valeur par valeur : `astype(str)` dépend de la version de
    # pandas (dtype `str` avec valeurs manquantes conservées en `NA` en pandas 3), ce
    # qui rendrait le hash fragile. `pd.isna` gère les manquants de façon uniforme.
    payload = "\n".join(
        ["|".join(columns)]
        + [
            "|".join("" if pd.isna(value) else str(value) for value in row)
            for row in ordered.itertuples(index=False, name=None)
        ]
    )
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()
    return {
        "source": config.SOURCE_REFERENCE,
        "n_observations": int(len(frame)),
        "n_colonnes": len(columns),
        "colonnes": columns,
        "hash_md5": digest,
        "version": f"{config.SOURCE_TABLE}@{digest[:12]}",
        "strategie": (
            "identifiant documenté (hash de tout le contenu : schéma et valeurs) ; "
            "DVC/lakeFS étudiés mais non retenus au MVP (volumes non justifiants)."
        ),
    }


def _flat_params(hyperparameters: dict[str, Any]) -> dict[str, str]:
    """Aplatit les hyperparamètres en chaînes (MLflow refuse les valeurs `None`)."""
    return {f"modele.{key}": str(value) for key, value in sorted(hyperparameters.items())}


def _log_metrics(result: dict[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {"entrainement_s": float(result["entrainement_s"])}
    for split_name in _SPLITS:
        block = result["metriques"][split_name]
        for suffix in _METRIC_SUFFIXES:
            if suffix in block and block[suffix] is not None:
                metrics[f"{suffix}_{split_name}"] = float(block[suffix])
    return metrics


def base_tags(
    *,
    dataset: dict[str, Any],
    code: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Tags communs à tous les runs (traçabilité dataset + code)."""
    code = code or code_version()
    return {
        "phase": "7 — Model registry",
        "source": str(dataset["source"]),
        "version_dataset": str(dataset["version"]),
        "hash_dataset": str(dataset["hash_md5"]),
        "n_observations": str(dataset["n_observations"]),
        "git_sha": str(code.get("git_sha")),
        "git_branch": str(code.get("git_branch")),
        "git_dirty": str(code.get("git_dirty")),
        "cible": config.TARGET,
        "devise": config.CURRENCY,
    }


def log_candidate_runs(
    results: dict[str, Any],
    *,
    dataset: dict[str, Any],
    tracking_uri: str | None = None,
    experiment: str | None = None,
    extra_tags: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Journalise un run par candidat (les 12 modèles de la Phase 6).

    Returns:
        ``{"experiment_id": ..., "runs": {slug: run_id}, "retenu": run_id}``.
    """
    configure(tracking_uri)
    experiment_id = ensure_experiment(experiment)
    tags = base_tags(dataset=dataset)
    if extra_tags:
        tags.update(extra_tags)
    code = code_version()
    meta = results["meta"]
    retained_slug = results["selection"]["slug"]

    run_ids: dict[str, str] = {}
    for slug, result in results["candidats"].items():
        with mlflow.start_run(
            experiment_id=experiment_id, run_name=slug, tags=tags
        ) as run:
            mlflow.set_tag("slug", slug)
            mlflow.set_tag("famille", str(result["famille"]))
            mlflow.set_tag("cible_transformee", str(result["cible_transformee"]))
            mlflow.set_tag("complexite", str(result["complexite"]))
            mlflow.set_tag("interpretabilite", str(result["interpretabilite"]))
            mlflow.set_tag("retenu", str(slug == retained_slug))
            mlflow.log_params(_flat_params(result["hyperparametres"]))
            mlflow.log_params(
                {
                    "graine": meta["graine"],
                    "n_features": len(meta["features"]),
                    "proportion_train": meta["proportions"]["train"],
                    "proportion_validation": meta["proportions"]["validation"],
                    "proportion_test": meta["proportions"]["test"],
                }
            )
            mlflow.log_metrics(_log_metrics(result))
            # Métriques par segment (validation) : journalisées comme artefact —
            # le nombre de quartiers rendrait un tag illisible.
            segments = result.get("segments_validation")
            if segments:
                mlflow.log_dict({"validation": segments}, "segments_validation.json")
            mlflow.set_tag("versions_logiciel", str(code["logiciel"]))
            run_ids[slug] = run.info.run_id

    return {
        "experiment_id": experiment_id,
        "runs": run_ids,
        "retenu": run_ids[retained_slug],
    }


def log_retained_model(
    *,
    run_id: str,
    model: Any,
    metadata: dict[str, Any],
    interval_path: Path | None = None,
    artifact_path: str = "modele",
) -> str:
    """Attache le modèle retenu et ses métadonnées au run correspondant.

    Returns:
        L'URI du modèle journalisé (utilisable pour l'enregistrement).
    """
    with mlflow.start_run(run_id=run_id):
        # `cloudpickle` et non `skops` : le pipeline retenu est un
        # `TransformedTargetRegressor` dont `func`/`inverse_func` sont des ufuncs
        # numpy, que skops refuse de sérialiser. Le modèle est le nôtre (aucun code
        # tiers chargé à la désérialisation), ce qui rend cloudpickle acceptable.
        info = mlflow.sklearn.log_model(
            model, name=artifact_path, serialization_format="cloudpickle"
        )
        mlflow.set_tag("modele_pipeline", metadata["nom"])
        mlflow.log_dict(metadata, "metadonnees.json")
        if interval_path is not None and Path(interval_path).exists():
            mlflow.log_artifact(str(interval_path))
        return info.model_uri


def tag_registered_model(*, run_id: str, etiquette: str) -> None:
    """Note sur le run le nom et la version du modèle enregistré.

    C'est le lien explicite entre le run d'entraînement et la version du registre
    (`rent-model-vN`) : sans lui, on saurait quel modèle a été servi mais pas
    d'où il vient.
    """
    mlflow.MlflowClient().set_tag(run_id, "modele_enregistre", etiquette)
