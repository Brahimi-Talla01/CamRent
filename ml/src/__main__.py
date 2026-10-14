"""CLI du ML : baselines (Phase 5) et modèles (Phase 6).

Exemple :

    python -m ml.src baselines --report docs/phase-5/baseline-report.md
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import run_baselines

logger = logging.getLogger("camrent.ml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ml.src",
        description="Phase 5 — baselines ML (moyenne globale, médiane par ville, "
        "médiane par quartier et type).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("baselines", help="évaluer les baselines et écrire le rapport")
    run_cmd.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="URL PostgreSQL (défaut : variable DATABASE_URL)",
    )
    run_cmd.add_argument(
        "--artifacts-dir",
        type=Path,
        default=None,
        help="dossier des artefacts régénérables (défaut : ml/artifacts)",
    )
    run_cmd.add_argument(
        "--metrics",
        type=Path,
        default=None,
        help="chemin du JSON de métriques",
    )
    run_cmd.add_argument(
        "--report",
        type=Path,
        default=None,
        help="chemin du rapport markdown",
    )
    run_cmd.add_argument("--verbose", action="store_true")

    models_cmd = sub.add_parser(
        "models",
        help="comparer les modèles, retenir le meilleur, valider la fourchette "
        "et sauvegarder (Phase 6)",
    )
    models_cmd.add_argument("--database-url", type=str, default=None)
    models_cmd.add_argument("--report", type=Path, default=None)
    models_cmd.add_argument("--selection", type=Path, default=None)
    models_cmd.add_argument("--models-dir", type=Path, default=None)
    models_cmd.add_argument(
        "--no-lightgbm", action="store_true", help="ignorer LightGBM (dépendance optionnelle)"
    )
    models_cmd.add_argument(
        "--no-persist", action="store_true", help="ne pas écrire le modèle retenu"
    )
    models_cmd.add_argument("--verbose", action="store_true")

    registry_cmd = sub.add_parser(
        "registry",
        help="journaliser les runs dans MLflow et enregistrer le modèle retenu "
        "(Phase 7)",
    )
    registry_cmd.add_argument("--database-url", type=str, default=None)
    registry_cmd.add_argument(
        "--tracking-uri", type=str, default=None, help="URI de suivi MLflow (défaut : env)"
    )
    registry_cmd.add_argument("--experiment", type=str, default=None)
    registry_cmd.add_argument("--report", type=Path, default=None)
    registry_cmd.add_argument("--models-dir", type=Path, default=None)
    registry_cmd.add_argument(
        "--no-lightgbm", action="store_true", help="ignorer LightGBM (dépendance optionnelle)"
    )
    registry_cmd.add_argument(
        "--no-persist", action="store_true", help="ne pas réécrire le modèle retenu"
    )
    registry_cmd.add_argument(
        "--no-register", action="store_true", help="journaliser sans enregistrer de version"
    )
    registry_cmd.add_argument("--verbose", action="store_true")
    return parser


def run_models_command(
    database_url: str | None,
    report_path: Path | None,
    selection_path: Path | None,
    models_dir: Path | None,
    *,
    include_lightgbm: bool,
    persist: bool,
) -> int:
    from . import run_models  # import local (scikit-learn chargé à la demande)

    try:
        results = run_models.run(
            database_url,
            report_path=report_path,
            metrics_path=selection_path,
            models_dir=models_dir,
            include_lightgbm=include_lightgbm,
            persist=persist,
        )
    except (RuntimeError, ValueError, OSError, KeyError) as exc:
        print(f"[ERREUR] modèles impossibles : {exc}", file=sys.stderr)
        return 1

    selection = results["selection"]
    threshold = results["seuil_reference"]
    intervals = results["intervalles"]
    retained_interval = intervals["methodes"][intervals["methode_retenue"]]["test"]
    print(f"[OK] {len(results['candidats'])} candidats comparés")
    for row in selection["classement"][:3]:
        print(
            f"     {row['slug']:26s} MAE validation {row['mae_validation']:>10,} "
            f"MedAE {row['medae_validation']:>9,} MAE test {row['mae_test']:>10,}"
        )
    verdict = "bat le seuil" if selection["bat_le_seuil_validation"] else "NE bat PAS le seuil"
    print(
        f"     retenu : {selection['slug']} — {verdict} "
        f"(seuil {threshold['mae_borne_basse_ic']:,} FCFA, gain "
        f"{selection['gain_vs_baseline_pct']} % vs `{threshold['baseline']}`)"
    )
    print(
        f"     fourchette : {intervals['methode_retenue']} — couverture test "
        f"{retained_interval['couverture_pct']} % (visé {intervals['niveau_vise_pct']} %), "
        f"largeur moyenne {retained_interval['largeur_moyenne']:,} FCFA"
    )
    top = results["explicabilite"]["importance_globale"][:3]
    print(
        "     facteurs principaux (erreur médiane supplémentaire) : "
        + ", ".join(
            f"{row['feature']} (+{row['erreur_mediane_supplementaire_moyenne']:,})"
            for row in top
        )
    )
    for name, path in results.get("artefacts", {}).items():
        print(f"     {name} : {path}")
    return 0


def run_registry_command(
    database_url: str | None,
    tracking_uri: str | None,
    experiment: str | None,
    report_path: Path | None,
    models_dir: Path | None,
    *,
    include_lightgbm: bool,
    persist: bool,
    register: bool,
) -> int:
    from . import run_registry  # import local (MLflow chargé à la demande)

    try:
        summary = run_registry.run(
            database_url,
            tracking_uri=tracking_uri,
            models_dir=models_dir,
            report_path=report_path,
            experiment=experiment,
            include_lightgbm=include_lightgbm,
            persist=persist,
            register=register,
        )
    except (RuntimeError, ValueError, OSError, KeyError) as exc:
        print(f"[ERREUR] registre impossible : {exc}", file=sys.stderr)
        return 1

    tracking = summary["tracking"]
    print(f"[OK] expérience `{tracking['experiment']}` (id {tracking['experiment_id']})")
    print(f"     {len(summary['runs'])} runs journalisés — URI {tracking['uri']}")
    print(f"     dataset {summary['dataset']['version']} "
          f"({summary['dataset']['n_observations']} observations)")
    if summary.get("registered"):
        registered = summary["registered"]
        print(
            f"     modèle enregistré : {registered['etiquette']} "
            f"(alias {registered['alias']}, promu {registered['promotion']})"
        )
    else:
        print("     aucun modèle enregistré")
    print(f"     rapport : {report_path or 'docs/phase-7/registry-report.md'}")
    return 0


def run(
    database_url: str | None,
    artifacts_dir: Path | None,
    metrics_path: Path | None,
    report_path: Path | None,
) -> int:
    try:
        results = run_baselines.run(
            database_url,
            artifacts_dir=artifacts_dir,
            metrics_path=metrics_path,
            report_path=report_path,
        )
    except (RuntimeError, ValueError, OSError, KeyError) as exc:
        print(f"[ERREUR] baselines impossibles : {exc}", file=sys.stderr)
        return 1

    primary = results["meta"]["scenario_principal"]
    scenario = results["scenarios"][primary]
    print(f"[OK] Scénario principal `{primary}` : {scenario['n_observations']} observations")
    for name, block in scenario["baselines"].items():
        validation = block["metriques"]["validation"]
        test = block["metriques"]["test"]
        print(
            f"     {name:24s} MAE validation {validation['mae']:>10,} "
            f"RMSE {validation['rmse']:>10,} R² {validation['r2']} | "
            f"MAE test {test['mae']:>10,}"
        )
    threshold = results["conclusion"]["seuil_reference"]
    print(
        f"     seuil à battre : MAE validation < {threshold['mae_borne_basse_ic']:,} FCFA "
        f"({threshold['gain_relatif_a_demontrer_pct']} % sous `{threshold['baseline']}`)"
    )
    print(
        f"     artefacts : {results['artefacts']['metriques']} / "
        f"{results['artefacts']['rapport']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.command == "baselines":
        return run(args.database_url, args.artifacts_dir, args.metrics, args.report)
    if args.command == "models":
        return run_models_command(
            args.database_url,
            args.report,
            args.selection,
            args.models_dir,
            include_lightgbm=not args.no_lightgbm,
            persist=not args.no_persist,
        )
    if args.command == "registry":
        return run_registry_command(
            args.database_url,
            args.tracking_uri,
            args.experiment,
            args.report,
            args.models_dir,
            include_lightgbm=not args.no_lightgbm,
            persist=not args.no_persist,
            register=not args.no_register,
        )
    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
