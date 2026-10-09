"""Document brut d'une source officielle — stocké **sans parsing**.

Pour les sources de référence officielles (MINFI, INS), dont les formats restent
à confirmer, on applique l'ELT le plus strict : on **conserve le document brut**
tel que téléchargé dans `data/raw/reference_data/`, et son interprétation est
différée. Aucun parseur fragile n'est embarqué.
"""

from __future__ import annotations

from collections.abc import Iterator

from ..models import RawRecord
from .base import SourceCollector

# Borne la taille conservée par document (le brut complet reste récupérable à la source).
MAX_DOCUMENT_CHARS = 200_000


class RawDocumentCollector(SourceCollector):
    NAME = "raw_document"

    def collect(self, limit: int | None = None) -> Iterator[RawRecord]:
        emitted = 0
        for url in self.spec.urls:
            if limit is not None and emitted >= limit:
                return
            response = self.http.fetch(url)
            yield RawRecord(
                source=self.spec.name,
                source_listing_id=url,
                url=url,
                fields={"kind": "raw_document", "content_type": response.content_type},
                raw_text=response.text[:MAX_DOCUMENT_CHARS],
            )
            emitted += 1
