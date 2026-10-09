"""Extraction et normalisation des valeurs de source (Phase 2).

Chaque fonction retourne une valeur **standardisée** à partir d'un libellé brut,
en signalant explicitement les valeurs **bornées** (préfixe ``>`` / ``≥``) plutôt
que de les présenter comme exactes.
"""

from __future__ import annotations

import re
from typing import Final

from .config import DEFAULT_PROPERTY_TYPE
from .geo import normalize_label

_BOUND_RE = re.compile(r"^\s*(?:>|≥|à partir de|starting from)\b", re.IGNORECASE)
_NO_PRICE_RE = re.compile(
    r"(?i)contact|sur\s*devis|sur\s*demande|no\s*price|n'?est\s*pas\s*indiqu"
)
_NUMBER_RE = re.compile(r"\d[\d\s\u00a0.,]*")
_DIGITS_ONLY_RE = re.compile(r"[^\d]")


def parse_price(raw: str | None) -> tuple[int | None, bool]:
    """Retourne ``(valeur, bornée)``. Une valeur bornée est un **minimum**, pas un prix exact."""
    text = (raw or "").strip()
    if not text or _NO_PRICE_RE.search(text):
        return None, False

    is_bound = bool(_BOUND_RE.match(text)) or bool(re.match(r"\s*[>≥]", text))
    match = _NUMBER_RE.search(text)
    if not match:
        return None, False

    digits = _DIGITS_ONLY_RE.sub("", match.group(0)).rstrip(".,")
    if not digits:
        return None, False
    return int(digits), is_bound


def parse_rooms(raw: str | None) -> tuple[int | None, bool]:
    """Retourne ``(nombre, borné)`` pour chambres ou salles de bain."""
    text = (raw or "").strip()
    if not text:
        return None, False
    is_bound = bool(re.match(r"\s*[>≥]", text))
    match = re.search(r"\d+", text)
    if not match:
        return None, False
    return int(match.group(0)), is_bound


AREA_RE = re.compile(r"(?i)(\d[\d\s\u00a0.,]*)\s*(?:m2|m²|metres?\s*carres?|sq\.?\s*m)")


def parse_area_m2(raw: str | None) -> float | None:
    match = AREA_RE.search(raw or "")
    if not match:
        return None
    digits = _DIGITS_ONLY_RE.sub("", match.group(1))
    return float(digits) if digits else None


# ---------------------------------------------------------------------------
# Type de bien
# ---------------------------------------------------------------------------
TYPE_ALIASES: Final[dict[str, str]] = {
    "studio": "studio",
    "appartement": "apartment",
    "apartment": "apartment",
    "appart": "apartment",
    "flat": "apartment",
    "chambre": "room",
    "room": "room",
    "villa": "house",
    "maison": "house",
    "house": "house",
    "bureau": "office",
    "office": "office",
    "boutique": "shop",
    "shop": "shop",
    "magasin": "warehouse",
    "entrepot": "warehouse",
    "warehouse": "warehouse",
    "store": "warehouse",
    "terrain": "land",
    "land": "land",
}

_TYPE_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
    alias: re.compile(rf"\b{re.escape(alias)}s?\b") for alias in TYPE_ALIASES
}


def normalize_property_type(raw: str | None) -> str:
    """Ramène un libellé de type (FR/EN) à une catégorie canonique."""
    lowered = normalize_label(raw or "")
    if not lowered:
        return DEFAULT_PROPERTY_TYPE
    for alias, canonical in TYPE_ALIASES.items():
        if _TYPE_PATTERNS[alias].search(lowered):
            return canonical
    return DEFAULT_PROPERTY_TYPE


YES_WORDS = re.compile(r"\b(?:oui|yes|with|true)\b", re.IGNORECASE)
NO_WORDS = re.compile(r"\b(?:non|no|sans|without|false)\b", re.IGNORECASE)


def parse_yes_no(raw: str | None) -> bool | None:
    """Convertit un libellé oui/non en booléen ; ``None`` si indéterminé."""
    text = (raw or "").strip()
    if not text:
        return None
    if NO_WORDS.search(text):
        return False
    if YES_WORDS.search(text):
        return True
    return None
