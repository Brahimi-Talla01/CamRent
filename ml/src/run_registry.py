"""Orchestration de la Phase 7 : journaliser les runs et enregistrer le modèle.

Enchaînement :

1. reconstruire les résultats de la Phase 6 (même séparation, mêmes candidats) et
   sauvegarder le modèle retenu sur disque ;
2. décrire la version du dataset (hash du contenu) et la version du code ;
3. journaliser un run MLflow par candidat dans l'expérience `rent_prediction` ;
4. attacher le modèle retenu à son run (modèle + intervalle + métadonnées) ;
5. enregistrer une version `rent-model-vN` et appliquer la règle de promotion ;
6. rendre le rapport markdown, entièrement dérivé du résumé.

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
) -> dict[str, Any]:
    """Exécute la Phase 7 de bout en bout et écrit le rapport."""
    frame = data.load_ml_dataset(database_url)
    results = run_models.build_results(
        frame,
        include_lightgbm=include_lightgbm,
        persist=persist,
        models_dir=models_dir,
    )
    dataset = tracking.dataset_version(frame)
    code = tracking.code_version()
    uri = tracking.configure(tracking_uri, database_url)
    experiment_name = experiment or config.MLFLOW_EXPERIMENT

    logged = tracking.log_candidate_runs(
        results, dataset=dataset, tracking_uri=uri, experiment=experiment_name
    )

    decision = registry.promotion_decision(results["selection"], results["seuil_reference"])
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
