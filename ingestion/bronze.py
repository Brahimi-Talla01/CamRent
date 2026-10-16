"""Validations **Bronze** : premières vérifications du brut collecté.

Contrôles demandés par la spec Phase 1 §4 :

- le fichier existe ;
- le nombre de lignes est raisonnable ;
- le JSON est valide ;
- la dernière collecte est récente (fraîcheur) ;
- les métadonnées du lot existent et concordent (volume).

Ces contrôles ne modifient jamais les données : ils rapportent un état.

Deux points d'entrée : ``check_lot()`` pour **un** lot (utilisé à la collecte,
avant l'écriture des métadonnées, pour consigner un statut de validation réel) et
``run_validations()`` pour l'ensemble de ``data/raw/`` — ce dernier ajoute le
contrôle de fraîcheur et la concordance avec les métadonnées de lot.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

from . import config, storage

REQUIRED_KEYS = ("source", "source_listing_id", "collected_at")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class BronzeReport:
    checks: list[Check]

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]

    @property
    def ok(self) -> bool:
        return not self.failures

    def summary(self) -> str:
        passed = sum(1 for c in self.checks if c.ok)
        return f"{passed}/{len(self.checks)} contrôles Bronze réussis"


def _read_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    """Retourne (enregistrements valides, erreurs de format)."""
    records: list[dict] = []
    errors: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                errors.append(f"{path.name}:{line_no} JSON invalide ({error.msg})")
    return records, errors


def _load_metadata_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    for meta_path in storage.iter_metadata_files():
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        raw_file = payload.get("raw_file")
        if isinstance(raw_file, str):
            index[raw_file] = payload
    return index


def _check_freshness(records_by_file: dict[str, list[dict]]) -> Check:
    newest: dt.datetime | None = None
    for records in records_by_file.values():
        for record in records:
            value = record.get("collected_at")
            if not isinstance(value, str):
                continue
            try:
                moment = dt.datetime.fromisoformat(value)
            except ValueError:
                continue
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=dt.UTC)
            if newest is None or moment > newest:
                newest = moment
    if newest is None:
        return Check("fraîcheur", False, "aucune date de collecte exploitable")
    age_days = (dt.datetime.now(dt.UTC) - newest).days
    ok = age_days <= config.FRESHNESS_MAX_DAYS
    return Check("fraîcheur", ok, f"collecte la plus récente : il y a {age_days} jour(s)")


def _lot_checks(
    rel: str,
    *,
    size: int,
    records: list[dict],
    errors: list[str],
    declared_count: int | None,
    expect_metadata: bool,
) -> list[Check]:
    """Contrôles Bronze d'un lot déjà lu (fonction pure, testable seule)."""
    checks = [
        Check("existence", size > 0, rel if size > 0 else f"{rel} est vide"),
        Check("format JSON", not errors, f"{rel} ({len(errors)} ligne(s) invalide(s))"),
        Check(
            "volume",
            len(records) >= config.MIN_REASONABLE_RECORDS,
            f"{rel} : {len(records)} observation(s)",
        ),
    ]

    missing = [
        key for key in REQUIRED_KEYS if any(key not in record for record in records)
    ]
    checks.append(Check("clés requises", not missing, f"{rel} manque : {missing or '—'}"))

    if expect_metadata:
        if declared_count is None:
            checks.append(Check("métadonnées", False, f"aucune métadonnée pour {rel}"))
        else:
            checks.append(
                Check(
                    "métadonnées",
                    declared_count == len(records),
                    f"{rel} : déclaré={declared_count} réel={len(records)}",
                )
            )
    return checks


def check_lot(raw_path: Path, *, expect_metadata: bool = False) -> BronzeReport:
    """Contrôles Bronze d'**un seul** lot, sans ses métadonnées par défaut.

    Utilisé à la collecte (les métadonnées du lot ne sont pas encore écrites) et
    par ``run_validations()`` pour chaque fichier brut.

    Args:
        raw_path: fichier brut JSONL.
        expect_metadata: exiger la présence et la concordance des métadonnées du
            lot (impossible avant leur écriture — d'où ``False`` par défaut).
    """
    rel = str(raw_path.relative_to(config.RAW_ROOT))
    records, errors = _read_jsonl(raw_path)
    metadata = _load_metadata_index().get(rel) if expect_metadata else None
    declared = metadata.get("record_count") if metadata else None
    return BronzeReport(
        _lot_checks(
            rel,
            size=raw_path.stat().st_size,
            records=records,
            errors=errors,
            declared_count=declared,
            expect_metadata=expect_metadata,
        )
    )


def run_validations() -> BronzeReport:
    """Exécute l'ensemble des contrôles Bronze sur `data/raw/`."""
    raw_files = sorted(storage.iter_raw_files())

    if not raw_files:
        return BronzeReport(
            [Check("présence", False, "aucun fichier brut dans data/raw/")]
        )

    metadata_index = _load_metadata_index()
    checks: list[Check] = []
    records_by_file: dict[str, list[dict]] = {}

    for path in raw_files:
        rel = str(path.relative_to(config.RAW_ROOT))
        records, errors = _read_jsonl(path)
        records_by_file[rel] = records
        metadata = metadata_index.get(rel)
        checks.extend(
            _lot_checks(
                rel,
                size=path.stat().st_size,
                records=records,
                errors=errors,
                declared_count=metadata.get("record_count") if metadata else None,
                expect_metadata=True,
            )
        )

    checks.append(_check_freshness(records_by_file))
    return BronzeReport(checks)
