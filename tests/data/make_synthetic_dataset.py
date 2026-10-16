"""Jeu de données **synthétique et déterministe** pour la CI (lot C).

Aucune donnée réelle n'est versionnable : `data/raw/`, `data/processed/` et
`data/samples/` sont ignorés par git, et le jeu local est un dépôt tiers **sans
licence** (redistribution interdite, `data/samples/README.md`). Pour exécuter les
tests de données (`dbt build`, 121 tests) en intégration continue, la CI fabrique
donc ses propres données : un jeu synthétique, généré localement, sans réseau ni
collecte — le port de droite de `pipelines/db.py`, qui est indifférent à la
provenance des lignes.

Ce script produit les **trois entrées** de `python -m pipelines load` :

    <data-root>/processed/silver_listings.parquet    (n lignes valides)
    <data-root>/processed/quarantine_listings.parquet (rejets, motifs variés)
    <data-root>/raw/metadata/<date>/*.json           (lots de collecte + provenance)

Le jeu satisfait explicitement les contrats de la Phase 4 (colonnes du Silver,
valeurs acceptées des tests dbt, bornes, unicité de `listing_key`) et couvre les
cas que les tests singuliers surveillent : un `bathrooms` hors borne **signalé**,
un lot **sans** provenance (`has_provenance = false`), des rejets des quatre
motifs, des groupes sous et au-dessus du seuil de publication (30).

Invariants respectés :

- **aucune écriture dans `data/` réel** — `--data-root` est obligatoire et la
  racine du projet est refusée (le Silver réel reste la source de vérité) ;
- **déterminisme** — même graine ⇒ même contenu ⇒ mêmes résultats `dbt build`
  (AGENTS.md §5 : reproductibilité) ;
- **aucune collecte réseau**, donc aucune porte légale à déclencher.

Usage (la CI) :

    python -m tests.data.make_synthetic_dataset --data-root "$RUNNER_TEMP/camrent-ci"
    CAMRENT_DATA_ROOT="$RUNNER_TEMP/camrent-ci" DATABASE_URL=... python -m pipelines load
    CAMRENT_DATA_ROOT=... DATABASE_URL=... dbt build

Exécution en **module** (`-m`) : le lancement direct par chemin ajouterait
`tests/data/` à la place de la racine du projet dans `sys.path`, et `pipelines`
n'y serait pas importable.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
from pathlib import Path

import pandas as pd

from pipelines import config

# Graine unique : le jeu est identique d'une exécution à l'autre.
DEFAULT_SEED = 20261009

# Date de collecte figée (valeur par défaut) : elle détermine `dim_date` et
# garantit que le rendu dbt ne bouge pas d'un jour à l'autre.
COLLECTED_AT = "2026-10-09T10:00:00+00:00"
COLLECTED_DAY = "2026-10-09"

NEIGHBORHOODS: dict[str, tuple[str, ...]] = {
    "Douala": ("Bonapriso", "Bonamoussadi", "Makepe", "Akwa", "Logpom"),
    "Yaoundé": ("Bastos", "Mvan", "Nsimeyong", "Etoudi", "Biyem-Assi"),
}

# Seuls des types réellement présents dans les valeurs acceptées dbt.
PROPERTY_TYPES: tuple[str, ...] = ("studio", "apartment", "house", "room")

SOURCES: tuple[str, ...] = ("reference_local", "koutchoumi")

QUARANTINE_REASONS: tuple[str, ...] = (
    "prix_manquant",
    "type_inconnu",
    "city_inconnue",
    "prix_invalide",
)

# Borne documentée de `ROOMS_MAX_PLAUSIBLE` (pipelines/config.py) : au-delà, la
# valeur reste dans le Silver et doit être signalée dans `outlier_flags`.
ROOMS_PLAUSIBLE_MAX = 10

SILVER_COLUMNS: tuple[str, ...] = config.SILVER_COLUMNS

QUARANTINE_COLUMNS: tuple[str, ...] = (
    *SILVER_COLUMNS,
    "quarantine_reason",
)


def _row(
    index: int,
    rng: random.Random,
) -> dict[str, object]:
    """Une observation Silver valide, tirée de façon déterministe."""
    city = "Douala" if rng.random() < 0.6 else "Yaoundé"
    neighborhood = rng.choice(NEIGHBORHOODS[city])
    property_type = rng.choice(PROPERTY_TYPES)
    source = SOURCES[0] if rng.random() < 0.7 else SOURCES[1]
    bedrooms = rng.randint(1, 5)
    bathrooms = rng.randint(0, 4)

    # Prix borné à la main : plausible (≥ 15 000), non extrême, et jamais nul —
    # le test dbt `within_range (min 1)` et `not_null` doivent passer.
    base = {"studio": 60_000, "room": 40_000, "apartment": 150_000, "house": 250_000}
    city_factor = 1.15 if city == "Douala" else 1.0
    rent_price = int(base[property_type] * city_factor * (0.75 + 0.5 * rng.random()))
    rent_price = max(15_000, rent_price)

    price_is_bound = rng.random() < 0.35
    if price_is_bound:
        rent_price = rent_price // 5_000 * 5_000

    return {
        "source": source,
        "source_file": f"{source} (ci)",
        "source_listing_id": f"ci-{index:06d}",
        "url": f"file://ci-synthetic/{index:06d}",
        "city": city,
        "neighborhood": neighborhood,
        "neighborhood_recognized": rng.random() < 0.9,
        "property_type": property_type,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "furnished": None,
        "parking": None,
        "gated": None,
        "area_m2": None,
        "rent_price": rent_price,
        "currency": "XAF",
        "price_is_bound": price_is_bound,
        "bedrooms_is_bound": False,
        "bathrooms_is_bound": False,
        "is_republication": rng.random() < 0.15,
        "outlier_flags": "",
        "posted_at": None,
        "collected_at": COLLECTED_AT,
    }


def build_silver(n_rows: int, seed: int) -> pd.DataFrame:
    """Le Silver synthétique — colonnes et types conformes à `SILVER_COLUMNS`."""
    rng = random.Random(seed)
    rows = [_row(index, rng) for index in range(n_rows)]

    # Une valeur hors borne **signalée** : c'est le cas que le test singulier
    # `assert_implausible_rooms_are_signalled` doit trouver (pas un échec).
    hors_borne = rows[n_rows // 2]
    hors_borne["bathrooms"] = ROOMS_PLAUSIBLE_MAX + 1
    hors_borne["outlier_flags"] = "bathrooms_outlier"

    # Quelques prix extrêmes conservés et signalés (jamais supprimés).
    for position in (n_rows // 3, (2 * n_rows) // 3):
        rows[position]["rent_price"] = 4_000_000
        rows[position]["outlier_flags"] = "price_outlier"

    frame = pd.DataFrame(rows, columns=list(SILVER_COLUMNS))
    frame["bedrooms"] = frame["bedrooms"].astype("int64")
    frame["bathrooms"] = frame["bathrooms"].astype("int64")
    frame["rent_price"] = frame["rent_price"].astype("int64")
    return frame


def build_quarantine(n_rows: int, seed: int) -> pd.DataFrame:
    """La quarantaine synthétique : les quatre motifs de rejet, jamais supprimés."""
    rng = random.Random(seed + 1)
    rows: list[dict[str, object]] = []
    for index in range(n_rows):
        reason = QUARANTINE_REASONS[index % len(QUARANTINE_REASONS)]
        source = SOURCES[index % len(SOURCES)]
        row: dict[str, object] = {
            "source": source,
            "source_file": f"{source} (ci)",
            "source_listing_id": f"ci-q-{index:06d}",
            "url": f"file://ci-synthetic/quarantine/{index:06d}",
            "city": "Douala" if rng.random() < 0.6 else "Yaoundé",
            "neighborhood": "Bonapriso",
            "neighborhood_recognized": True,
            "property_type": "apartment",
            "bedrooms": 2,
            "bathrooms": 1,
            "furnished": None,
            "parking": None,
            "gated": None,
            "area_m2": None,
            "rent_price": 100_000,
            "currency": "XAF",
            "price_is_bound": False,
            "bedrooms_is_bound": False,
            "bathrooms_is_bound": False,
            "is_republication": False,
            "outlier_flags": "",
            "posted_at": None,
            "collected_at": COLLECTED_AT,
            "quarantine_reason": reason,
        }
        # Les rejets correspondent réellement à leur motif.
        if reason == "prix_manquant":
            row["rent_price"] = None
        elif reason == "type_inconnu":
            row["property_type"] = None
        elif reason == "city_inconnue":
            row["city"] = None
            row["neighborhood"] = None
            row["property_type"] = None
        else:  # prix_invalide
            row["rent_price"] = 0
        rows.append(row)

    frame = pd.DataFrame(rows, columns=list(QUARANTINE_COLUMNS))
    for column in ("bedrooms", "bathrooms"):
        frame[column] = frame[column].astype("float64")
    return frame


def build_metadata(seed: int) -> list[tuple[str, dict[str, object]]]:
    """Trois lots de collecte : avec provenance, sans provenance, en échec."""
    rng = random.Random(seed + 2)
    provenance = {
        "connector_version": "0.1.0",
        "content_bytes": 4096,
        "content_sha256": f"{rng.getrandbits(256):064x}",
        "lot_validation_status": "ok",
        "lot_validation_failures": [],
    }
    lots = [
        (
            "koutchoumi_100000",
            {
                **provenance,
                "source": "koutchoumi",
                "category": "listings",
                "method": "http_get_html_parse",
                "format": "jsonl",
                "collected_at": COLLECTED_AT,
                "collected_day": COLLECTED_DAY,
                "record_count": 40,
                "raw_file": f"listings/{COLLECTED_DAY}/koutchoumi_100000.jsonl",
                "urls": ["https://example.invalid/"],
                "rights_status": "uncertain",
                "rights_notice": "Synthétique (CI) — aucune collecte réseau.",
                "notes": "jeu de CI",
            },
        ),
        # Lot antérieur à la provenance renforcée : `has_provenance` doit être
        # faux, pas inventé (lot B).
        (
            "reference_local_100001",
            {
                "source": "reference_local",
                "category": "reference_data",
                "method": "local_csv_read",
                "format": "jsonl",
                "collected_at": COLLECTED_AT,
                "collected_day": COLLECTED_DAY,
                "record_count": 40,
                "raw_file": f"reference_data/{COLLECTED_DAY}/reference_local_100001.jsonl",
                "urls": [],
                "rights_status": "local",
                "rights_notice": "Synthétique (CI).",
                "notes": "jeu de CI, lot sans provenance",
            },
        ),
        (
            "geloka_100002",
            {
                **provenance,
                "lot_validation_status": "failed",
                "lot_validation_failures": ["volume"],
                "source": "geloka",
                "category": "reference_data",
                "method": "http_get_html_parse",
                "format": "jsonl",
                "collected_at": COLLECTED_AT,
                "collected_day": COLLECTED_DAY,
                "record_count": 1,
                "raw_file": f"reference_data/{COLLECTED_DAY}/geloka_100002.jsonl",
                "urls": ["https://example.invalid/"],
                "rights_status": "uncertain",
                "rights_notice": "Synthétique (CI).",
                "notes": "jeu de CI, lot en échec de validation",
            },
        ),
    ]
    return lots


def generate(
    data_root: Path,
    *,
    silver_rows: int,
    quarantine_rows: int,
    seed: int,
) -> dict[str, object]:
    """Écrit les trois entrées du chargeur sous `data_root` (récursif, sûr)."""
    processed = data_root / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    silver = build_silver(silver_rows, seed)
    quarantine = build_quarantine(quarantine_rows, seed)
    silver_path = processed / config.SILVER_FILENAME
    quarantine_path = processed / config.QUARANTINE_FILENAME
    silver.to_parquet(silver_path, index=False)
    quarantine.to_parquet(quarantine_path, index=False)

    metadata_dir = data_root / "raw" / "metadata" / COLLECTED_DAY
    metadata_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, payload in build_metadata(seed):
        path = metadata_dir / f"{name}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(path))

    return {
        "silver": str(silver_path),
        "silver_rows": int(len(silver)),
        "quarantine": str(quarantine_path),
        "quarantine_rows": int(len(quarantine)),
        "metadata_files": len(written),
    }


def _assert_not_project_data_root(data_root: Path) -> None:
    """Refuse d'écrire dans `data/` du projet : le Silver réel n'est pas écrasable."""
    project_data = (Path(__file__).resolve().parents[2] / "data").resolve()
    if data_root.resolve() == project_data:
        raise SystemExit(
            f"Refus d'écrire dans {project_data} : ce jeu est synthétique et ne doit "
            "jamais remplacer les données réelles. Passer --data-root <répertoire "
            "dédié, ex. $RUNNER_TEMP/camrent-ci>."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="make_synthetic_dataset",
        description="Génère le jeu synthétique de la CI (Silver, quarantaine, lots).",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="répertoire cible (obligatoire : jamais data/ du projet)",
    )
    parser.add_argument("--silver-rows", type=int, default=360)
    parser.add_argument("--quarantine-rows", type=int, default=48)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    _assert_not_project_data_root(args.data_root)
    result = generate(
        args.data_root,
        silver_rows=args.silver_rows,
        quarantine_rows=args.quarantine_rows,
        seed=args.seed,
    )
    stamp = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    print(f"[OK] jeu synthétique généré à {stamp}")
    print(f"     silver      : {result['silver_rows']} lignes → {result['silver']}")
    print(f"     quarantaine : {result['quarantine_rows']} lignes → {result['quarantine']}")
    print(f"     lots        : {result['metadata_files']} fichiers de métadonnées")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
