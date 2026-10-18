"""Enregistrement et promotion du modèle retenu (Phase 7).

Responsabilité unique : transformer un run journalisé en **version de modèle
enregistrée** (`rent-model-vN`) et appliquer la **règle de promotion** écrite ici.
Aucun modèle n'est considéré comme servi tant qu'il n'est pas enregistré ; aucun
modèle n'est promu au statut de référence (`alias champion`) s'il ne satisfait
pas toutes les conditions de la règle.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
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


def require_promotion_approval(
    decision: dict[str, Any], *, approved_by: str | None = None
) -> None:
    """Refuse une promotion non approuvée explicitement.

    La règle de promotion est évaluée par le code, mais elle ne décide pas seule :
    un humain portant le rôle d'administrateur doit fournir son identité. Sans
    approbation, aucune version ne devient servable — l'alias de référence n'est
    jamais déplacé automatiquement.

    Raises:
        ValueError: la règle est satisfaite mais aucune approbation n'est fournie.
    """
    if decision.get("promotion") and not (approved_by or "").strip():
        raise ValueError(
            "Promotion refusée : la règle de promotion est satisfaite mais aucune "
            "approbation explicite n'a été fournie. Relancer avec "
            "`--confirm-promotion --approved-by <nom>` (rôle administrateur) ; "
            "aucun alias de référence n'est déplacé automatiquement."
        )


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
    approved_by: str | None = None,
    pin_path: Path | None = None,
) -> dict[str, Any]:
    """Crée une version `rent-model-vN` et pose l'alias champion si promu.

    La promotion exige une **approbation explicite** (`approved_by`) : une règle
    satisfaite sans approbation lève une erreur, sans rien écrire dans le registre.
    Lorsqu'une version est promue, la version servie est **épinglée** dans
    `ml/models/champion.json` (fichier versionné).

    Returns:
        Description de la version enregistrée (nom, numéro, étiquette, alias,
        décision de promotion, approbation, chemin d'épinglage).
    """
    require_promotion_approval(decision, approved_by=approved_by)
    name = name or config.REGISTERED_MODEL_NAME
    _registry_backend_available()
    client = MlflowClient()
    version = mlflow.register_model(model_uri, name)
    number = str(version.version)

    approuve_le = datetime.now(UTC).isoformat(timespec="seconds")
    tags = {
        "famille": str(metadata["famille"]),
        "cible_transformee": str(metadata["cible_transformee"]),
        "graine": str(metadata["graine"]),
        "features": ", ".join(metadata["features"]),
        "version_dataset": str(dataset["version"]),
        "hash_dataset": str(dataset["hash_md5"]),
        "git_sha": str(code.get("git_sha")),
        "promu": str(decision["promotion"]),
        "approuve_par": str(approved_by or ""),
        "approuve_le": approuve_le if decision["promotion"] else "",
    }
    for key, value in tags.items():
        client.set_model_version_tag(name, number, key, value)

    description = (
        f"Modèle retenu en Phase 6 ({metadata['famille']}, cible "
        f"{metadata['cible_transformee']}) — promu : {decision['promotion']}."
    )
    client.update_model_version(name=name, version=number, description=description)

    alias = None
    pinned: Path | None = None
    if decision["promotion"]:
        client.set_registered_model_alias(name, config.REGISTERED_MODEL_ALIAS, number)
        alias = config.REGISTERED_MODEL_ALIAS
        pinned = write_champion_pin(
            {
                "name": name,
                "version": int(version.version),
                "etiquette": f"{name}-v{number}",
                "alias": alias,
                "run_id": run_id,
                "model_uri": model_uri,
                "approuve_par": approved_by,
                "approuve_le": approuve_le,
            },
            dataset=dataset,
            code=code,
            path=pin_path,
        )

    return {
        "name": name,
        "version": int(version.version),
        "etiquette": f"{name}-v{number}",
        "alias": alias,
        "run_id": run_id,
        "model_uri": model_uri,
        "promotion": decision["promotion"],
        "approuve_par": approved_by if decision["promotion"] else None,
        "approuve_le": approuve_le if decision["promotion"] else None,
        "epingle": str(pinned) if pinned else None,
    }


def write_champion_pin(
    registered: dict[str, Any],
    *,
    dataset: dict[str, Any],
    code: dict[str, Any],
    path: Path | None = None,
) -> Path:
    """Écrit le fichier **versionné** qui épingle la version servie.

    C'est le seul lien vérifiable, depuis le dépôt, entre le code et la version
    effectivement servie : le registre MLflow vit dans une base locale non
    versionnée. Aucun secret n'y est écrit (pas d'URI de suivi, pas de mot de passe).
    """
    path = path or config.CHAMPION_PIN_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pin_version": 1,
        "nom": registered["name"],
        "version": registered["version"],
        "etiquette": registered["etiquette"],
        "alias": registered["alias"],
        "run_id": registered["run_id"],
        "model_uri": registered["model_uri"],
        "dataset": {
            "source": dataset["source"],
            "version": dataset["version"],
            "hash_md5": dataset["hash_md5"],
            "n_observations": dataset["n_observations"],
        },
        "git_sha": code.get("git_sha"),
        "approuve_par": registered.get("approuve_par"),
        "approuve_le": registered.get("approuve_le"),
        "ecrit_le": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


# Clés sans lesquelles le pin ne décrit pas une version servable ni ses données.
REQUIRED_PIN_KEYS: tuple[str, ...] = ("nom", "version", "etiquette", "model_uri", "dataset")
REQUIRED_DATASET_KEYS: tuple[str, ...] = ("source", "version", "hash_md5")


def read_champion_pin(path: Path | None = None) -> dict[str, Any]:
    """Relit la version épinglée, sans jamais tolérer un pin douteux.

    Un pin absent, illisible ou incomplet rend la provenance du modèle servi
    invérifiable : la lecture échoue explicitement plutôt que de laisser servir
    une version dont on ne sait plus ce qu'elle décrit.

    Raises:
        FileNotFoundError: aucun fichier de pin à l'emplacement attendu.
        ValueError: contenu non JSON, format inattendu ou clé de provenance
            manquante.
    """
    pin_path = Path(path) if path is not None else config.CHAMPION_PIN_PATH
    if not pin_path.is_file():
        raise FileNotFoundError(
            f"Version épinglée introuvable : {pin_path}. Relancer "
            "`python -m ml.src registry --confirm-promotion --approved-by <nom>` "
            "pour épingler la version servie."
        )
    try:
        payload = json.loads(pin_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Version épinglée illisible : {pin_path}.") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Version épinglée illisible (format inattendu) : {pin_path}.")
    missing = [key for key in REQUIRED_PIN_KEYS if not payload.get(key)]
    if missing:
        raise ValueError(
            f"Version épinglée incomplète ({', '.join(missing)}) : {pin_path}."
        )
    dataset = payload["dataset"]
    if not isinstance(dataset, dict):
        raise ValueError(f"Provenance du pin illisible (dataset) : {pin_path}.")
    missing_dataset = [key for key in REQUIRED_DATASET_KEYS if not dataset.get(key)]
    if missing_dataset:
        raise ValueError(
            "Provenance du pin incomplète "
            f"(dataset.{', dataset.'.join(missing_dataset)}) : {pin_path}."
        )
    return payload
