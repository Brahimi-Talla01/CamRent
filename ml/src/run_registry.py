"""Orchestration de la Phase 7 : journaliser les runs et enregistrer le modèle.

Enchaînement :

1. reconstruire les résultats de la Phase 6 (même séparation, mêmes candidats) et
   sauvegarder le modèle retenu sur disque ;
2. décrire la version du dataset (hash du contenu) et la version du code ;
3. évaluer la règle de promotion **avant toute écriture** et exiger, si la règle est
   satisfaite, une **approbation explicite** (`--confirm-promotion --approved-by <nom>`) ;
4. journaliser un run MLflow par candidat dans l'expérience `rent_prediction` ;
5. attacher le modèle retenu à son run (modèle + intervalle + métadonnées) ;
6. enregistrer une version `rent-model-vN`, appliquer la règle de promotion et
   **épingler** la version servie dans `ml/models/champion.json` ;
7. rendre le rapport markdown, entièrement dérivé du résumé.

Le résumé retourné ne contient que des valeurs sérialisables ; le modèle
enregistré vit dans le registre MLflow (PostgreSQL), non versionné.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import (
    config,
    data,
    persistence,
    registry,
    registry_report,
    run_models,
    tracking,
)


def build_summary(
    results: dict[str, Any],
    *,
    dataset: dict[str, Any],
    code: dict[str, Any],
    logged: dict[str, Any],
    tracking_uri: str,
    experiment: str,
    decision: dict[str, Any],
    registered: dict[str, Any] | None,
) -> dict[str, Any]:
    """Assemble le résumé sérialisable du registre (source du rapport)."""
    return {
        "meta": {
            "phase": "7 — Model registry",
            "source": config.SOURCE_REFERENCE,
            "cible": config.TARGET,
            "devise": config.CURRENCY,
            "graine": results["meta"]["graine"],
        },
        "dataset": dataset,
        "code": code,
        "tracking": {
            # Le rapport est versionné : jamais de mot de passe dedans.
            "uri": tracking.mask_tracking_uri(tracking_uri),
            "experiment": experiment,
            "experiment_id": logged["experiment_id"],
        },
        "runs": logged["runs"],
        "selection": results["selection"],
        "seuil_reference": results["seuil_reference"],
        "promotion": decision,
        "registered": registered,
    }


def run(
    database_url: str | None = None,
    *,
    tracking_uri: str | None = None,
    models_dir: Path | None = None,
    report_path: Path | None = None,
    experiment: str | None = None,
    include_lightgbm: bool = True,
    persist: bool = True,
    register: bool = True,
    approved_by: str | None = None,
) -> dict[str, Any]:
    """Exécute la Phase 7 de bout en bout et écrit le rapport.

    Args:
        approved_by: identité de l'administrateur qui approuve la promotion. Sans
            elle, une règle satisfaite interrompt l'exécution **avant** toute
            écriture dans le registre (aucune version, aucun alias déplacé).
    """
    frame = data.load_ml_dataset(database_url)
    results = run_models.build_results(
        frame,
        include_lightgbm=include_lightgbm,
        persist=persist,
        models_dir=models_dir,
    )
    dataset = tracking.dataset_version(frame)
    code = tracking.code_version()

    # Gouvernance : la règle est évaluée avant toute écriture. Une règle satisfaite
    # sans approbation explicite interrompt l'exécution, pour qu'aucune version ne
    # soit enregistrée ni promue par inadvertance.
    decision = registry.promotion_decision(results["selection"], results["seuil_reference"])
    if register:
        registry.require_promotion_approval(decision, approved_by=approved_by)

    uri = tracking.configure(tracking_uri, database_url)
    experiment_name = experiment or config.MLFLOW_EXPERIMENT

    logged = tracking.log_candidate_runs(
        results, dataset=dataset, tracking_uri=uri, experiment=experiment_name
    )

    registered: dict[str, Any] | None = None
    artifacts = results.get("artefacts", {})
    if persist and "modele" in artifacts:
        model = persistence.load_model(Path(artifacts["modele"]))
        metadata = persistence.load_metadata(Path(artifacts["metadonnees"]))
        interval = artifacts.get("intervalle")
        model_uri = tracking.log_retained_model(
            run_id=logged["retenu"],
            model=model,
            metadata=metadata,
            interval_path=Path(interval) if interval else None,
        )
        if register:
            registered = registry.register(
                model_uri=model_uri,
                run_id=logged["retenu"],
                metadata=metadata,
                decision=decision,
                dataset=dataset,
                code=code,
                approved_by=approved_by,
            )
        if registered:
            tracking.tag_registered_model(
                run_id=logged["retenu"], etiquette=registered["etiquette"]
            )

    summary = build_summary(
        results,
        dataset=dataset,
        code=code,
        logged=logged,
        tracking_uri=uri,
        experiment=experiment_name,
        decision=decision,
        registered=registered,
    )

    report_path = report_path or config.REGISTRY_REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    report_path.write_text(
        registry_report.render_report(summary, generated_at=generated_at), encoding="utf-8"
    )
    return summary
