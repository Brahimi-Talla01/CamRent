"""Référentiel géographique (seed curé) — ville et quartiers canoniques.

Approche retenue (décision Phase 2) : un **seed curé** des quartiers connus de
Douala et Yaoundé, complété par une résolution tolérante (accents, casse,
séparateurs) et un rapprochement flou. Les valeurs non reconnues ne sont **pas**
supprimées : elles sont conservées telles quelles et signalées
(`neighborhood_recognized = False`) pour enrichir le référentiel plus tard.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Final

# ---------------------------------------------------------------------------
# Villes
# ---------------------------------------------------------------------------
CITY_ALIASES: Final[dict[str, str]] = {
    "douala": "Douala",
    "yaounde": "Yaoundé",
    "yaoundé": "Yaoundé",
}


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_label(text: str) -> str:
    """Normalise un libellé : accents, casse, séparateurs → un espace unique."""
    lowered = strip_accents(text or "").lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def resolve_city(raw: str) -> str | None:
    """Retourne la ville canonique, ou ``None`` si hors périmètre."""
    tokens = normalize_label(raw).split()
    for token in tokens:
        if token in CITY_ALIASES:
            return CITY_ALIASES[token]
    normalized = normalize_label(raw)
    for alias, canonical in CITY_ALIASES.items():
        if alias in normalized:
            return canonical
    return None


# ---------------------------------------------------------------------------
# Quartiers canoniques (seed)
# ---------------------------------------------------------------------------
CANONICAL_NEIGHBORHOODS: Final[dict[str, tuple[str, ...]]] = {
    "Douala": (
        "Akwa",
        "Bonanjo",
        "Bonapriso",
        "Bonamoussadi",
        "Bonaberi",
        "Bali",
        "Deido",
        "Makepe",
        "Makepe Missoke",
        "Ndogbong",
        "Logpom",
        "Logbessou",
        "Beedi",
        "Bepanda",
        "New Bell",
        "Ndokotti",
        "Cité des Palmiers",
        "Kotto",
        "Ndogpassi",
        "Nyalla",
        "Yassa",
        "Japoma",
        "Mbanga Bakaka",
        "Mabanda",
        "Bassa",
        "Denibakari",
        "Nylon",
        "Zone Industrielle",
        "Pk 12",
        "Pk 14",
        "Pk 16",
        "Pk 17",
        "Pk 18",
        "Pk 21",
    ),
    "Yaoundé": (
        "Bastos",
        "Nlongkak",
        "Elig-Essono",
        "Mvog-Mbi",
        "Mvog-Ada",
        "Mvog-Betsi",
        "Nsam",
        "Biyem-Assi",
        "Mendong",
        "Ekounou",
        "Emana",
        "Odza",
        "Nkolbisson",
        "Etoudi",
        "Etoa-Meki",
        "Mvan",
        "Mimboman",
        "Djoungolo",
        "Centre-Ville",
        "Essos",
        "Nsimeyong",
        "Damas",
        "Ngousso",
        "Ekoudou",
        "Mbankolo",
        "Mfandena",
        "Tsinga",
        "Ngoa-Ekelle",
        "Nkolndongo",
    ),
}

# Variantes observées → canonique (en plus de la correspondance directe).
EXTRA_ALIASES: Final[dict[str, str]] = {
    "akwa nord": "Akwa",
    "newbell": "New Bell",
    "nouveau bell": "New Bell",
    "bonamoussadi douala": "Bonamoussadi",
    "makepe missoke": "Makepe Missoke",
    "etoudi": "Etoudi",
    "elig essono": "Elig-Essono",
    "mvog mbi": "Mvog-Mbi",
    "mvog ada": "Mvog-Ada",
    "mvog betsi": "Mvog-Betsi",
    "biyem assi": "Biyem-Assi",
    "eto a meki": "Etoa-Meki",
    "etoa meki": "Etoa-Meki",
    "centre ville": "Centre-Ville",
    "ngo a ekelle": "Ngoa-Ekelle",
}


def _build_lookup() -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for city, names in CANONICAL_NEIGHBORHOODS.items():
        city_map = {normalize_label(name): name for name in names}
        lookup[city] = city_map
    return lookup


_LOOKUP: Final[dict[str, dict[str, str]]] = _build_lookup()

# Séparateurs fréquents : « Quartier », « Qr », « - ».
_NEIGHBORHOOD_PREFIXES = re.compile(r"\b(quartier|qtr|qr|neighborhood|zone)\b", re.IGNORECASE)


def _clean_neighborhood(raw: str) -> str:
    text = _NEIGHBORHOOD_PREFIXES.sub(" ", raw or "")
    text = re.sub(r"\s+", " ", text.replace("/", " ").replace("-", " ")).strip()
    return text


def resolve_neighborhood(raw: str, city: str) -> tuple[str, bool]:
    """Résout un quartier vers sa forme canonique.

    Retourne ``(valeur, reconnue)``. Si le quartier n'est pas reconnu, la valeur
    d'origine nettoyée est conservée et ``reconnue`` vaut ``False``.
    """
    cleaned = _clean_neighborhood(raw)
    if not cleaned:
        return "", False

    normalized = normalize_label(cleaned)
    for prefix in ("douala", "yaounde", "yaoundé"):
        if normalized.startswith(prefix + " "):
            normalized = normalized[len(prefix) + 1 :]

    if not normalized:
        return cleaned, False

    city_map = _LOOKUP.get(city, {})
    if normalized in city_map:
        return city_map[normalized], True
    if normalized in EXTRA_ALIASES:
        return EXTRA_ALIASES[normalized], True

    candidates = difflib.get_close_matches(normalized, list(city_map), n=1, cutoff=0.85)
    if candidates:
        return city_map[candidates[0]], True

    return cleaned, False
