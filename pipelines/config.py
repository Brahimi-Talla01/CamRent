"""Configuration des pipelines de transformation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DATA_ROOT: Final[Path] = Path(os.environ.get("CAMRENT_DATA_ROOT", PROJECT_ROOT / "data"))
RAW_ROOT: Final[Path] = DATA_ROOT / "raw"
PROCESSED_ROOT: Final[Path] = DATA_ROOT / "processed"

SILVER_FILENAME: Final[str] = "silver_listings.parquet"
QUARANTINE_FILENAME: Final[str] = "quarantine_listings.parquet"

# Villes du MVP.
CITIES: Final[tuple[str, ...]] = ("Douala", "Yaoundé")

# Bornes de plausibilité (signalement d'aberrations — pas de suppression).
PRICE_MIN_PLAUSIBLE: Final[int] = int(os.environ.get("CAMRENT_PRICE_MIN", "10000"))
PRICE_MAX_PLAUSIBLE: Final[int] = int(os.environ.get("CAMRENT_PRICE_MAX", "2000000"))
ROOMS_MAX_PLAUSIBLE: Final[int] = int(os.environ.get("CAMRENT_ROOMS_MAX", "10"))

CURRENCY: Final[str] = "XAF"
DEFAULT_PROPERTY_TYPE: Final[str] = "unknown"

# Schéma de sortie Silver (ordre des colonnes).
SILVER_COLUMNS: Final[tuple[str, ...]] = (
    "source",
    "source_file",
    "source_listing_id",
    "url",
    "city",
    "neighborhood",
    "property_type",
    "bedrooms",
    "bathrooms",
    "furnished",
    "parking",
    "gated",
    "area_m2",
    "rent_price",
    "currency",
    "price_is_bound",
    "bedrooms_is_bound",
    "bathrooms_is_bound",
    "is_republication",
    "neighborhood_recognized",
    "outlier_flags",
    "posted_at",
    "collected_at",
)
