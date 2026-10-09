"""Modèles bruts de l'ingestion.

Règle Phase 1 : on capture la donnée **telle qu'observée**, sans normalisation.
Les valeurs issues de la source restent dans ``fields`` (non transformées) ; la
mise au schéma cible (ville canonique, `property_type`, unités…) est une
transformation de la **Phase 2**.

Un ``RawRecord`` = une observation élémentaire : une annonce pour les sources de
listings, un segment/médiane pour un baromètre, une ligne pour un jeu local, un
document pour une source officielle.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from typing import Any


def now_iso() -> str:
    """Horodatage UTC au format ISO 8601."""
    return dt.datetime.now(dt.UTC).isoformat()


@dataclass
class RawRecord:
    """Observation brute, préservée sans transformation."""

    source: str
    source_listing_id: str
    url: str
    collected_at: str = field(default_factory=now_iso)
    posted_at: str | None = None               # date fournie par la source, si présente
    fields: dict[str, Any] = field(default_factory=dict)  # valeurs de source, non normalisées
    raw_text: str = ""                         # extrait brut utile au rejeu (Phase 2)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
