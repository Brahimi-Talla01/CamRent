"""CLI d'ingestion.

Exemples :

    python -m ingestion --list-sources
    python -m ingestion --source reference_local
    python -m ingestion --source geloka --confirm-legal "CGU vérifiées le 2026-10-09"
    python -m ingestion --source koutchoumi --confirm-legal "..." --limit 40
    python -m ingestion --validate-bronze
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import bronze, config
from .http_client import LegalGateError, RobotsDisallowed
from .sources import COLLECTORS
from .storage import RawJsonlWriter, write_metadata

logger = logging.getLogger("camrent.ingestion")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingestion",
        description="Collecte des données brutes CamRent (Phase 1) et validations Bronze.",
    )
    parser.add_argument("--source", choices=sorted(config.SOURCES), help="source à collecter")
    parser.add_argument("--list-sources", action="store_true", help="afficher le registre")
    parser.add_argument("--validate-bronze", action="store_true", help="valider data/raw/")
    parser.add_argument(
        "--confirm-legal",
        metavar="AVERTISSEMENT",
        help="confirme que robots.txt + CGU ont été vérifiés (obligatoire pour les sources "
        "non 'verified'/'local')",
    )
    parser.add_argument("--limit", type=int, default=None, help="nombre max d'observations")
    parser.add_argument("--verbose", action="store_true")
    return parser


def list_sources() -> None:
    print(f"{'SOURCE':<18}{'CATÉGORIE':<16}{'DROITS':<12}URL")
    print("-" * 100)
    for spec in config.SOURCES.values():
        url = spec.urls[0] if spec.urls else "(local)"
        print(f"{spec.name:<18}{spec.category:<16}{spec.rights:<12}{url}")
    print("\n" + config.RIGHTS_HELP)


def run_collect(name: str, confirm_legal: str | None, limit: int | None) -> int:
    spec = config.SOURCES[name]
    if spec.requires_confirm and not confirm_legal:
        print(
            f"[LÉGAL] '{name}' est de droits '{spec.rights}' : {spec.rights_notice}\n"
            f"Relance avec --confirm-legal \"<phrase>\". {config.RIGHTS_HELP}",
            file=sys.stderr,
        )
        return 2

    collector_cls = COLLECTORS[name]
    writer = RawJsonlWriter(category=spec.category, source=name)
    failure: Exception | None = None
    try:
        collector = collector_cls(spec, confirm_legal=confirm_legal)
        for record in collector.collect(limit=limit):
            writer.write(record)
    except LegalGateError as error:
        writer.abort()
        print(f"[LÉGAL] {error}", file=sys.stderr)
        return 2
    except RobotsDisallowed as error:
        writer.abort()
        print(f"[ROBOTS] {error}", file=sys.stderr)
        return 3
    except Exception as error:  # une erreur réseau/parsing conserve le brut déjà écrit
        failure = error
        logger.exception("collecte interrompue pour %s", name)
    finally:
        writer.close()

    if writer.count == 0:
        writer.abort()
        print(f"[VIDE] {name} : aucune observation collectée", file=sys.stderr)
        return 1

    notes = "" if failure is None else f"collecte interrompue : {failure}"
    metadata_path = write_metadata(spec, writer, list(spec.urls), notes)
    print(f"[OK] {name} : {writer.count} observation(s) brute(s)")
    print(f"     brut      : {writer.path}")
    print(f"     métadonnées : {metadata_path}")
    return 0


def run_validate_bronze() -> int:
    report = bronze.run_validations()
    for check in report.checks:
        mark = "OK" if check.ok else "KO"
        print(f"[{mark}] {check.name:<14} {check.detail}")
    print(report.summary())
    return 0 if report.ok else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.list_sources:
        list_sources()
        return 0
    if args.validate_bronze:
        return run_validate_bronze()
    if not args.source:
        build_parser().print_help()
        return 1
    return run_collect(args.source, args.confirm_legal, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
