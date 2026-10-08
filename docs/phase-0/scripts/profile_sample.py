"""Profilage et analyse exploratoire de l'échantillon de Phase 0.

Source des données :
    https://github.com/deegeorgie/Predicting-house-prices-in-Cameroon
    (fichiers ``koutchoumi1.csv`` et ``jumia.csv``, branche ``master``).
    Le dépôt source ne déclare aucune licence.

Dépendances : bibliothèque standard Python uniquement (pas de pandas).

Usage :
    python docs/phase-0/scripts/profile_sample.py data/samples
"""

from __future__ import annotations

import csv
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

OTHER_CURRENCIES = ("€", "$", "EUR", "USD")


def parse_int(raw: str) -> int | None:
    """Extrait un entier d'un texte (prix, chambres, salles de bain)."""
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else None


def percentile(sorted_values: list[int], p: float) -> float:
    """Percentile par interpolation linéaire (p entre 0 et 1)."""
    if not sorted_values:
        return float("nan")
    index = (len(sorted_values) - 1) * p
    low, high = math.floor(index), math.ceil(index)
    if low == high:
        return float(sorted_values[int(index)])
    return sorted_values[low] * (high - index) + sorted_values[high] * (index - low)


def fmt(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def print_distribution(label: str, values: list[str], top: int = 8) -> None:
    print(f"-- {label} --")
    counter = Counter(v for v in values if v)
    for value, count in counter.most_common(top):
        print(f"  {value!r}: {count}")
    print(f"  (distinctes: {len(counter)})")


def print_median_by(label: str, groups: dict[str, list[int]]) -> None:
    print(f"-- {label} --")
    for key, values in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:8]:
        print(f"  {key!r}: n={len(values)} médiane={fmt(statistics.median(values))}")


def column_summary(name: str, values: list[str]) -> None:
    total = len(values)
    empty = sum(1 for value in values if not value.strip())
    distinct = len({value.strip() for value in values})
    print(f"  - {name!r}: {distinct} distinctes, {empty} vides ({empty / total:.1%})")
    for value, count in Counter(v.strip() for v in values if v.strip()).most_common(2):
        print(f"      top: {value!r} ({count})")


def split_area(area: str, source: str) -> tuple[str, str]:
    """(ville, quartier). Koutchoumi 'Douala/Makepe' ; Jumia 'Bonapriso, Douala, Littoral'."""
    parts = [p.strip() for p in re.split(r"[/,]", area) if p.strip()]
    if not parts:
        return "", ""
    if source == "koutchoumi":
        return parts[0], (parts[1] if len(parts) > 1 else "")
    city = parts[-2] if len(parts) >= 2 else parts[0]
    return city, parts[0]


def analyse(path: Path) -> int:
    fields, rows = read_rows(path)
    print(f"\n{'=' * 70}\nFICHIER: {path.name}\n{'=' * 70}")
    print(f"lignes: {len(rows)}  colonnes: {len(fields)} -> {fields}")

    print("\n-- Valeurs manquantes / cardinalité --")
    for field in fields:
        column_summary(field, [row.get(field, "") or "" for row in rows])

    exact = len(rows) - len({tuple(sorted(row.items())) for row in rows})
    print(f"\n-- Doublons: {exact} lignes strictement identiques --")

    price_field = "Price" if "Price" in fields else fields[-1]
    raw_prices = [row.get(price_field, "") or "" for row in rows]

    print("\n-- Loyer (Price) --")
    prices = [p for p in (parse_int(v) for v in raw_prices) if p is not None]
    print(f"  exploitables: {len(prices)} / {len(raw_prices)}")
    if prices:
        ordered = sorted(prices)
        print(f"  min={fmt(ordered[0])}  p25={fmt(percentile(ordered, 0.25))}  "
              f"médiane={fmt(statistics.median(ordered))}  p75={fmt(percentile(ordered, 0.75))}  "
              f"max={fmt(ordered[-1])}")
        print(f"  moyenne={fmt(statistics.mean(ordered))}")
        print(f"  <=0: {sum(1 for p in prices if p <= 0)}  <20k: {sum(1 for p in prices if p < 20000)}  "
              f">2M: {sum(1 for p in prices if p > 2000000)}")

    area_field = "Area" if "Area" in fields else "Address"
    source = "koutchoumi" if area_field == "Area" else "jumia"
    pairs = [split_area(row.get(area_field, "") or "", source) for row in rows]
    print()
    print_distribution("Ville", [city for city, _ in pairs])
    print()
    print_distribution("Quartier", [hood for _, hood in pairs])

    by_city: dict[str, list[int]] = defaultdict(list)
    for (city, _), raw in zip(pairs, raw_prices):
        value = parse_int(raw)
        if value is not None:
            by_city[city].append(value)
    print()
    print_median_by("Loyer médian par ville", by_city)

    bedrooms_field = "Bedrooms"
    if bedrooms_field in fields:
        by_bedrooms: dict[str, list[int]] = defaultdict(list)
        for row, raw in zip(rows, raw_prices):
            value, bedrooms = parse_int(raw), parse_int(row.get(bedrooms_field, "") or "")
            if value is not None and bedrooms is not None:
                by_bedrooms[str(bedrooms)].append(value)
        print()
        print_median_by("Loyer médian par chambres", by_bedrooms)

    if "Type" in fields:
        print()
        print_distribution("Type (brut)", [row.get("Type", "") or "" for row in rows], top=6)

    return len(rows)


def main(sample_dir: str) -> int:
    directory = Path(sample_dir)
    files = sorted(directory.glob("*.csv"))
    if not files:
        print(f"Aucun CSV dans {directory}", file=sys.stderr)
        return 1
    total = sum(analyse(path) for path in files)
    print(f"\n{'=' * 70}\nTOTAL: {total} lignes sur {len(files)} fichier(s)\n{'=' * 70}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "data/samples"))
