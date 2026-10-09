"""Jeu de référence **local** (`data/samples/*.csv`) — aucun réseau.

Provient du dépôt tiers `deegeorgie` (sans licence déclarée) : usage **local
uniquement**, non redistribué (cf. `docs/phase-0/legal-assessment.md`). Chaque
ligne est capturée telle quelle, sans normalisation.

Ce collecteur ne fait aucun accès réseau : il ne relève donc pas de la porte
légale de collecte.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator

from .. import config
from ..models import RawRecord
from .base import SourceCollector


class ReferenceLocalCollector(SourceCollector):
    NAME = "reference_local"

    def collect(self, limit: int | None = None) -> Iterator[RawRecord]:
        emitted = 0
        for csv_path in sorted(config.SAMPLES_ROOT.glob("*.csv")):
            with csv_path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for index, row in enumerate(reader):
                    if limit is not None and emitted >= limit:
                        return
                    fields: dict[str, object] = {"source_file": csv_path.name}
                    fields.update({key: value for key, value in row.items() if key})
                    yield RawRecord(
                        source=self.NAME,
                        source_listing_id=f"{csv_path.stem}-{index:06d}",
                        url=f"file://{csv_path.name}",
                        fields=fields,
                    )
                    emitted += 1
