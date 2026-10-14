"""Enregistrement et promotion du modèle retenu (Phase 7).

Responsabilité unique : transformer un run journalisé en **version de modèle
enregistrée** (`rent-model-vN`) et appliquer la **règle de promotion** écrite ici.
Aucun modèle n'est considéré comme servi tant qu'il n'est pas enregistré ; aucun
modèle n'est promu au statut de référence (`alias champion`) s'il ne satisfait
pas toutes les conditions de la règle.
"""

from __future__ import annotations

from typing import Any

import mlflow
from mlflow import MlflowClient

from . import config

# Règle de promotion — écrite et applicable (spec 07, étape 4).
PROMOTION_CONDITIONS: tuple[tuple[str, str], ...] = (
    (
        "bat_la_baseline",
        "Le modèle bat `baseline_neighborhood` sur la graine de référence et sur "
        "toutes les séparations de robustesse (aucun gain de hasard).",
    ),
    (
        "seuil_phase_5",
        "La MAE de validation passe sous le seuil de référence de la Phase 5 "
        "(borne basse de l'intervalle de confiance à 95 %).",
    ),
    (
        "reproductible",
        "Le résultat est confirmé sur au moins deux séparations (graines fixes) et "
        "la version du code comme la version du dataset sont consignées dans le run.",
    ),
)


def promotion_rule() -> dict[str, Any]:
    """Règle de promotion, sous forme sérialisable (reprise dans le rapport)."""
    return {
        "conditions": [
            {"id": identifier, "libelle": libelle} for identifier, libelle in PROMOTION_CONDITIONS
        ],
        "portee": (
            "La promotion rend le modèle servable (`alias champion`) ; elle est "
            "**explicite** : aucun déploiement automatique."
        ),
    }


def promotion_decision(
    selection: dict[str, Any], threshold: dict[str, Any]
) -> dict[str, Any]:
    """Évalue la règle de promotion sur le modèle retenu.

    Returns:
        ``{"promotion": bool, "conditions": [...], "regle": {...}}`` — chaque
        condition porte son identifiant, son résultat et un détail chiffré.
    """
    robustness = selection.get("robustesse", {})
    nb_seeds = int(robustness.get("nb_graines", 0))
    nb_beat = int(robustness.get("nb_graines_battant_la_baseline", 0))
    gain = float(selection.get("gain_vs_baseline_pct", 0.0))

    conditions = [
        {
            "id": "bat_la_baseline",
            "satisfait": gain > 0 and nb_seeds > 0 and nb_beat == nb_seeds,
            "detail": (
                f"gain {gain} % sur la graine de référence ; baseline battue sur "
                f"{nb_beat}/{nb_seeds} séparations"
            ),
        },
        {
            "id": "seuil_phase_5",
            "satisfait": bool(selection["bat_le_seuil_validation"]),
            "detail": (
                f"MAE validation {selection['mae_validation']} FCFA vs seuil "
                f"{threshold['mae_borne_basse_ic']} FCFA ({threshold['baseline']})"
            ),
        },
        {
            "id": "reproductible",
            "satisfait": nb_seeds >= 2,
            "detail": (
                f"{nb_seeds} séparations évaluées ; version du code et version du "
                "dataset journalisées dans le run"
            ),
        },
    ]
    return {
        "promotion": all(condition["satisfait"] for condition in conditions),
        "conditions": conditions,
        "regle": promotion_rule(),
    }


def _registry_backend_available() -> None:
    """Le Model Registry exige un backend base de données (pas un file store)."""
    uri = mlflow.get_tracking_uri() or ""
    if uri.startswith("file:") or "://" not in uri:
        raise ValueError(
            "Le Model Registry MLflow exige un backend base de données. "
            "Définir `MLFLOW_TRACKING_URI` (ex. `postgresql+psycopg://…/mlflow`) "
            f"au lieu du file store local « {uri} »."
        )


def register(
    *,
    model_uri: str,
    run_id: str,
    metadata: dict[str, Any],
    decision: dict[str, Any],
    dataset: dict[str, Any],
    code: dict[str, Any],
    name: str | None = None,
) -> dict[str, Any]:
    """Crée une version `rent-model-vN` et pose l'alias champion si promu.

    Returns:
        Description de la version enregistrée (nom, numéro, étiquette, alias,
        décision de promotion).
    """
    name = name or config.REGISTERED_MODEL_NAME
    _registry_backend_available()
    client = MlflowClient()
    version = mlflow.register_model(model_uri, name)
    number = str(version.version)

    tags = {
        "famille": str(metadata["famille"]),
        "cible_transformee": str(metadata["cible_transformee"]),
        "graine": str(metadata["graine"]),
        "features": ", ".join(metadata["features"]),
        "version_dataset": str(dataset["version"]),
        "hash_dataset": str(dataset["hash_md5"]),
        "git_sha": str(code.get("git_sha")),
        "promu": str(decision["promotion"]),
    }
    for key, value in tags.items():
        client.set_model_version_tag(name, number, key, value)

    description = (
        f"Modèle retenu en Phase 6 ({metadata['famille']}, cible "
        f"{metadata['cible_transformee']}) — promu : {decision['promotion']}."
    )
    client.update_model_version(name=name, version=number, description=description)

    alias = None
    if decision["promotion"]:
        client.set_registered_model_alias(name, config.REGISTERED_MODEL_ALIAS, number)
        alias = config.REGISTERED_MODEL_ALIAS

    return {
        "name": name,
        "version": int(version.version),
        "etiquette": f"{name}-v{number}",
        "alias": alias,
        "run_id": run_id,
        "model_uri": model_uri,
        "promotion": decision["promotion"],
    }
