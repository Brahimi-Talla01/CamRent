"""CLI des baselines ML (Phase 5).

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
    return parser


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
    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
