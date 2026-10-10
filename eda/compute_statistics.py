"""Calcule les statistiques de l'EDA (Phase 3) depuis le Silver dataset.

Lit ``data/processed/silver_listings.parquet`` et écrit ``eda/statistics.json``.
Les statistiques sont calculées ici (source unique de vérité) puis mises en
forme par ``generate_reports.py`` : aucun chiffre n'est écrit en dur dans les
rapports.

Limites de périmètre (Phase 3) :
- Aucun entraînement de modèle.
- Aucun data leakage : pas de ``rent_per_m2`` (``area_m2`` entièrement absent).
- Aucune imputation : les valeurs manquantes sont signalées, jamais remplies.
- Les valeurs aberrantes sont signalées, jamais supprimées.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent
STATS_PATH = OUT_DIR / "statistics.json"
SILVER_PATH = Path("data/processed/silver_listings.parquet")

# Seuil d'observations minimal pour publier une médiane par quartier.
MIN_NEIGHBORHOOD_N = 30
# Seuil sous lequel un quartier est signalé comme sous-représenté.
LOW_VOLUME_N = 10

# Colonnes non exploitables car entièrement vides dans le Silver actuel.
MISSING_MARKERS = ("furnished", "parking", "gated", "area_m2", "posted_at")


def _json_default(value: Any) -> Any:
    """Rend les scalaires numpy sérialisables en JSON."""
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Type non sérialisable en JSON : {type(value)!r}")


def _group_stats(
    df: pd.DataFrame,
    key: str,
    columns: tuple[str, ...],
    total: int | None = None,
) -> list[dict[str, Any]]:
    """Agrège ``rent_price`` par ``key`` en une liste de dictionnaires."""
    agg = df.groupby(key)["rent_price"].agg(list(columns)).round(0).reset_index()
    records: list[dict[str, Any]] = []
    for row in agg.to_dict(orient="records"):
        record: dict[str, Any] = {key: row[key]}
        for column in columns:
            value = row[column]
            record[column] = int(value) if column == "count" else float(value)
        if total:
            record["share"] = round(100.0 * record["count"] / total, 2)
        records.append(record)
    records.sort(key=lambda item: item["count"], reverse=True)
    return records


def _bedrooms_block(df: pd.DataFrame) -> dict[str, Any]:
    summary = df["bedrooms"]
    agg = (
        df.groupby("bedrooms")["rent_price"]
        .agg(["count", "median", "mean"])
        .round(0)
        .reset_index()
    )
    by_value = [
        {
            "bedrooms": int(row["bedrooms"]),
            "count": int(row["count"]),
            "median": float(row["median"]),
            "mean": float(row["mean"]),
        }
        for row in agg.to_dict(orient="records")
    ]
    return {
        "count": int(summary.count()),
        "mean": float(summary.mean()),
        "median": float(summary.median()),
        "min": float(summary.min()),
        "max": float(summary.max()),
        "zeros": int((summary == 0).sum()),
        "by_value": by_value,
    }


def _bathrooms_block(df: pd.DataFrame) -> dict[str, Any]:
    summary = df["bathrooms"]
    return {
        "count": int(summary.count()),
        "mean": float(summary.mean()),
        "median": float(summary.median()),
        "min": float(summary.min()),
        "max": float(summary.max()),
        "zeros": int((summary == 0).sum()),
    }


def _outliers_block(df: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, int]]:
    flags = df["outlier_flags"].fillna("").astype(str).str.strip()
    mask = flags != ""
    columns = ["source", "city", "property_type", "rent_price", "outlier_flags"]
    records = [
        {
            "source": row["source"],
            "city": row["city"],
            "property_type": row["property_type"],
            "rent_price": int(row["rent_price"]),
            "outlier_flags": row["outlier_flags"],
        }
        for row in df.loc[mask, columns].to_dict(orient="records")
    ]
    counter: Counter[str] = Counter()
    for value in flags[mask]:
        for flag in value.split(","):
            if flag:
                counter[flag] += 1
    summary = {"total": int(mask.sum()), **{key: int(v) for key, v in counter.items()}}
    return records, summary


def _neighborhood_block(df: pd.DataFrame, total: int) -> dict[str, Any]:
    counts = df["neighborhood"].value_counts()
    median = df.groupby("neighborhood")["rent_price"].median().round(0)
    mean = df.groupby("neighborhood")["rent_price"].mean().round(0)
    bound_share = df.groupby("neighborhood")["price_is_bound"].mean().mul(100).round(1)

    def rows(names: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "neighborhood": name,
                "count": int(counts[name]),
                "median": float(median[name]),
                "mean": float(mean[name]),
                "bound_share": float(bound_share[name]),
            }
            for name in names
        ]

    reliable = median[
        df.groupby("neighborhood")["rent_price"].count() >= MIN_NEIGHBORHOOD_N
    ]
    low_volume = counts[counts <= LOW_VOLUME_N]
    return {
        "total": int(counts.size),
        "recognized": int(df["neighborhood_recognized"].sum()),
        "not_recognized": int((~df["neighborhood_recognized"]).sum()),
        "top_by_count": rows(counts.head(5).index.tolist()),
        "most_expensive": rows(reliable.sort_values(ascending=False).head(5).index.tolist()),
        "most_affordable": rows(reliable.sort_values().head(5).index.tolist()),
        "min_n_threshold": MIN_NEIGHBORHOOD_N,
        "low_volume_threshold": LOW_VOLUME_N,
        "low_volume_neighborhoods": int(low_volume.size),
        "low_volume_rows": int(low_volume.sum()),
        "single_observation_neighborhoods": int((counts == 1).sum()),
        "top5_share": round(100.0 * counts.head(5).sum() / total, 1),
        "top10_share": round(100.0 * counts.head(10).sum() / total, 1),
        "unrecognized_list": sorted(
            df.loc[~df["neighborhood_recognized"], "neighborhood"].unique().tolist()
        ),
    }


def _city_neighborhood_block(df: pd.DataFrame) -> dict[str, Any]:
    """Contrôle de cohérence : un quartier canonique n'appartient qu'à une ville."""
    recognized = df[df["neighborhood_recognized"]]
    per_city = recognized.groupby("city")["neighborhood"].nunique()
    cross = recognized.groupby("neighborhood")["city"].nunique()
    return {
        "recognized_total": int(recognized["neighborhood"].nunique()),
        "by_city": [
            {"city": city, "count": int(count)} for city, count in per_city.items()
        ],
        "cross_city_conflicts": int((cross > 1).sum()),
    }


def compute_statistics(path: Path = SILVER_PATH) -> dict[str, Any]:
    df = pd.read_parquet(path, engine="fastparquet")
    total = len(df)

    rent = df["rent_price"]
    log_rent = np.log1p(rent)
    correlations = df[["rent_price", "bedrooms", "bathrooms"]].corr().round(3)

    missing_counts = df.isna().sum()
    missing = [
        {
            "column": column,
            "missing_count": int(missing_counts[column]),
            "share": round(100.0 * int(missing_counts[column]) / total, 2),
        }
        for column in df.columns
        if int(missing_counts[column]) > 0
    ]

    outliers, outlier_summary = _outliers_block(df)
    empty_columns = [column for column in df.columns if df[column].isna().all()]
    constant_columns = [
        column for column in df.columns if df[column].nunique(dropna=False) <= 1
    ]

    return {
        "dataset": {
            "source_path": str(path),
            "total_rows": int(total),
            "column_count": int(df.shape[1]),
            "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        },
        "rent_price": {
            "count": int(rent.count()),
            "mean": float(rent.mean()),
            "median": float(rent.median()),
            "std": float(rent.std()),
            "min": float(rent.min()),
            "max": float(rent.max()),
            "q25": float(rent.quantile(0.25)),
            "q75": float(rent.quantile(0.75)),
            "skewness": float(rent.skew()),
            "kurtosis": float(rent.kurtosis()),
            "zeros": int((rent == 0).sum()),
            "negatives": int((rent < 0).sum()),
        },
        "log_target": {
            "log1p": {
                "mean": float(log_rent.mean()),
                "median": float(log_rent.median()),
                "std": float(log_rent.std()),
                "skewness": float(log_rent.skew()),
            }
        },
        "city": _group_stats(
            df, "city", ("count", "mean", "median", "min", "max", "std"), total
        ),
        "property_type": _group_stats(
            df, "property_type", ("count", "mean", "median", "min", "max"), total
        ),
        "neighborhood_recognized": _group_stats(
            df, "neighborhood_recognized", ("count", "mean", "median")
        ),
        "is_republication": _group_stats(
            df, "is_republication", ("count", "median"), total
        ),
        "price_is_bound": _group_stats(df, "price_is_bound", ("count", "median"), total),
        "source": _group_stats(
            df, "source", ("count", "mean", "median", "max"), total
        ),
        "bedrooms": _bedrooms_block(df),
        "bathrooms": _bathrooms_block(df),
        "missing": missing,
        "empty_columns": empty_columns,
        "constant_columns": constant_columns,
        "unavailable_features": [c for c in MISSING_MARKERS if c in empty_columns],
        "outliers": outliers,
        "outlier_summary": outlier_summary,
        "correlations": {
            "variables": ["rent_price", "bedrooms", "bathrooms"],
            "matrix": correlations.to_dict(),
        },
        "neighborhood": _neighborhood_block(df, total),
        "city_neighborhood": _city_neighborhood_block(df),
    }


def main() -> None:
    stats = compute_statistics()
    STATS_PATH.write_text(
        json.dumps(stats, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    print(f"Wrote {STATS_PATH} ({STATS_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
