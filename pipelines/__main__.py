"""CLI des pipelines CamRent.

Exemple :

    python -m pipelines silver --report docs/phase-2/cleaning-report.md
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import config, report, silver

logger = logging.getLogger("camrent.pipelines")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipelines", description="Transformations CamRent (Phase 2 — Silver)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    silver_cmd = sub.add_parser("silver", help="construire le Silver dataset depuis le Raw")
    silver_cmd.add_argument("--raw-root", type=Path, default=None, help="racine du Raw")
    silver_cmd.add_argument("--out-dir", type=Path, default=None, help="dossier de sortie")
    silver_cmd.add_argument("--report", type=Path, default=None, help="chemin du rapport (md)")
    silver_cmd.add_argument("--verbose", action="store_true")
    return parser


def run_silver(raw_root: Path | None, out_dir: Path | None, report_path: Path | None) -> int:
    records = silver.load_raw_records(raw_root)
    if not records:
        print(
            f"[VIDE] aucune donnée brute sous {(raw_root or config.RAW_ROOT)} "
            "(lancer d'abord `python -m ingestion`)",
            file=sys.stderr,
        )
        return 1

    result = silver.build(records)
    paths = silver.write_outputs(result, out_dir)

    print(f"[OK] Silver : {result.stats['silver_rows']} lignes → {paths['silver']}")
    print(f"     quarantine : {result.stats['quarantine_rows']} lignes → {paths['quarantine']}")
    print(f"     par source : {result.stats['by_source']}")
    print(f"     par ville  : {result.stats['by_city']}")

    if report_path is not None:
        report.write_report(result, report_path)
        print(f"     rapport    : {report_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.command == "silver":
        return run_silver(args.raw_root, args.out_dir, args.report)
    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
