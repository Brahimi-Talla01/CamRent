"""Construction du **Silver dataset** depuis le Raw immuable.

Étapes : adaptation par source → résolution (ville/quartier/type) → validation →
déduplication → signalement d'aberrations → écriture (`data/processed/`).

Aucune donnée n'est supprimée : les observations invalides sont routées vers la
**quarantine** avec leur motif ; les valeurs extrêmes valides restent dans le
Silver avec un drapeau (`outlier_flags`).
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config
from .adapters import Candidate, adapt
from .geo import resolve_city, resolve_neighborhood
from .parsing import normalize_property_type

# ---------------------------------------------------------------------------
# Lecture du Raw
# ---------------------------------------------------------------------------


def load_raw_records(raw_root: Path | None = None) -> list[dict]:
    """Lit tous les enregistrements brut (`listings/` + `reference_data/`)."""
    root = raw_root or config.RAW_ROOT
    records: list[dict] = []
    for category in ("listings", "reference_data"):
        for path in sorted((root / category).glob("*/*.jsonl")):
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Résultat
# ---------------------------------------------------------------------------
@dataclass
class CleanResult:
    silver: list[dict[str, Any]] = field(default_factory=list)
    quarantine: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


def _resolve(candidate: Candidate) -> dict[str, Any]:
    city = resolve_city(candidate.city_raw)
    neighborhood, recognized = resolve_neighborhood(
        candidate.neighborhood_raw, city or ""
    )
    return {
        "city": city,
        "neighborhood": neighborhood,
        "neighborhood_recognized": recognized,
        "property_type": normalize_property_type(candidate.property_type_raw),
    }


def _validate(row: dict[str, Any]) -> str | None:
    """Retourne un motif d'invalidation, ou ``None`` si l'observation est valide."""
    if not row["city"]:
        return "city_inconnue"
    if not row["neighborhood"]:
        return "quartier_manquant"
    if row["property_type"] == config.DEFAULT_PROPERTY_TYPE:
        return "type_inconnu"
    price = row["rent_price"]
    if price is None:
        return "prix_manquant"
    if price <= 0:
        return "prix_invalide"
    for key in ("bedrooms", "bathrooms"):
        value = row[key]
        if value is not None and value < 0:
            return f"{key}_invalide"
    if row["area_m2"] is not None and row["area_m2"] <= 0:
        return "surface_invalide"
    return None


def _outlier_flags(row: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    price = row["rent_price"]
    if price is not None and not (
        config.PRICE_MIN_PLAUSIBLE <= price <= config.PRICE_MAX_PLAUSIBLE
    ):
        flags.append("price_outlier")
    for key in ("bedrooms", "bathrooms"):
        value = row[key]
        if value is not None and value > config.ROOMS_MAX_PLAUSIBLE:
            flags.append(f"{key}_outlier")
    return flags


def _similarity_key(row: dict[str, Any]) -> str:
    return "|".join(
        str(row.get(key, ""))
        for key in ("city", "neighborhood", "property_type", "bedrooms", "bathrooms", "rent_price")
    )


def _to_silver_row(candidate: Candidate, resolved: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": candidate.source,
        "source_file": candidate.source_file,
        "source_listing_id": candidate.source_listing_id,
        "url": candidate.url,
        "city": resolved["city"],
        "neighborhood": resolved["neighborhood"],
        "property_type": resolved["property_type"],
        "bedrooms": candidate.bedrooms,
        "bathrooms": candidate.bathrooms,
        "furnished": None,
        "parking": None,
        "gated": None,
        "area_m2": candidate.area_m2,
        "rent_price": candidate.rent_price,
        "currency": config.CURRENCY,
        "price_is_bound": candidate.price_is_bound,
        "bedrooms_is_bound": candidate.bedrooms_is_bound,
        "bathrooms_is_bound": candidate.bathrooms_is_bound,
        "is_republication": False,
        "neighborhood_recognized": resolved["neighborhood_recognized"],
        "outlier_flags": "",
        "posted_at": candidate.posted_at,
        "collected_at": candidate.collected_at,
    }


def build(records: Iterable[dict]) -> CleanResult:
    """Construit le Silver dataset à partir des enregistrements brut."""
    result = CleanResult()
    reasons: Counter[str] = Counter()
    seen_ids: set[tuple[str, str, str]] = set()
    seen_keys: set[str] = set()
    by_source: Counter[str] = Counter()
    by_city: Counter[str] = Counter()

    records_read = 0
    adapted = 0
    for record in records:
        records_read += 1
        candidate = adapt(record)
        if candidate is None:
            continue
        adapted += 1

        id_key = (candidate.source, candidate.source_file, candidate.source_listing_id)
        if id_key in seen_ids:
            reasons["doublon_technique"] += 1
            continue
        seen_ids.add(id_key)

        row = _to_silver_row(candidate, _resolve(candidate))
        reason = _validate(row)
        if reason is not None:
            reasons[reason] += 1
            result.quarantine.append({**row, "quarantine_reason": reason})
            continue

        key = _similarity_key(row)
        if key in seen_keys:
            row["is_republication"] = True
            reasons["republication"] += 1
        else:
            seen_keys.add(key)

        row["outlier_flags"] = ",".join(_outlier_flags(row))
        result.silver.append(row)
        by_source[candidate.source_file or candidate.source] += 1
        by_city[row["city"]] += 1

    result.stats = {
        "records_read": records_read,
        "adapted": adapted,
        "silver_rows": len(result.silver),
        "quarantine_rows": len(result.quarantine),
        "reasons": dict(sorted(reasons.items())),
        "by_source": dict(sorted(by_source.items())),
        "by_city": dict(sorted(by_city.items())),
        "price_bound": sum(1 for row in result.silver if row["price_is_bound"]),
        "outliers": sum(1 for row in result.silver if row["outlier_flags"]),
        "neighborhood_unrecognized": sum(
            1 for row in result.silver if not row["neighborhood_recognized"]
        ),
    }
    return result


# ---------------------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------------------
def write_outputs(result: CleanResult, out_dir: Path | None = None) -> dict[str, Path]:
    """Écrit Silver et quarantine en Parquet (fichiers écrasables : zone dérivée)."""
    import pandas as pd  # import local : évite pandas pour les tests unitaires purs

    out = out_dir or config.PROCESSED_ROOT
    out.mkdir(parents=True, exist_ok=True)

    silver_path = out / config.SILVER_FILENAME
    quarantine_path = out / config.QUARANTINE_FILENAME

    pd.DataFrame(result.silver, columns=list(config.SILVER_COLUMNS)).to_parquet(
        silver_path, index=False
    )
    quarantine_columns = [*config.SILVER_COLUMNS, "quarantine_reason"]
    pd.DataFrame(result.quarantine, columns=quarantine_columns).to_parquet(
        quarantine_path, index=False
    )
    return {"silver": silver_path, "quarantine": quarantine_path}
