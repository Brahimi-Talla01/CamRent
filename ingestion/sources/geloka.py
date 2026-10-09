"""Geloka — baromètre des loyers (données **agrégées**).

La page publique expose des médianes par (ville, type de bien) et une fourchette,
sur N annonces analysées. Chaque segment devient un ``RawRecord`` de catégorie
`reference_data` : ce n'est **pas** une annonce individuelle, mais un point de
repère pour valider les tendances (jamais une observation d'entraînement).

Les valeurs sont conservées telles quelles : la normalisation est en Phase 2.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from html.parser import HTMLParser

from ..models import RawRecord
from .base import SourceCollector

URL = "https://www.geloka.com/fr/rent-barometer"

# « À Douala, le loyer médian d'un appartement est de 300 000 FCFA par mois
#   (8 octobre 2026), dans une fourchette de 60 000 à 1 500 000 FCFA, sur 32
#   annonces analysées par Geloka. »
_SENTENCE_RE = re.compile(
    r"À\s(?P<city>[A-ZÉÈ][\wéèêàç'\-]+),\sle\sloyer\smédian\s(?P<article>d['e]un|de\sla|d['e]une)\s"
    r"(?P<type>[\wéèêàç\-]+)\sest\sde\s(?P<price>[\d\s\u00a0]+)\sFCFA\spar\smois\s"
    r"\((?P<date>[^)]+)\),\sdans\sune\sfourchette\sde\s(?P<low>[\d\s\u00a0]+)\sà\s"
    r"(?P<high>[\d\s\u00a0]+)\sFCFA,\ssur\s(?P<n>\d+)\sannonces\sanalysées\spar\sGeloka\.",
    re.IGNORECASE,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.chunks.append(data.strip())


def _visible_text(html: str) -> str:
    extractor = _TextExtractor()
    extractor.feed(html)
    return "\n".join(extractor.chunks)


def _digits(value: str) -> int:
    return int(re.sub(r"[^\d]", "", value))


def parse_barometer(html: str, url: str) -> Iterator[RawRecord]:
    """Extrait les segments du baromètre depuis le HTML (sans réseau → testable)."""
    for match in _SENTENCE_RE.finditer(_visible_text(html)):
        city = match.group("city")
        property_type = match.group("type")
        yield RawRecord(
            source="geloka",
            source_listing_id=f"{city.lower()}-{property_type.lower()}",
            url=url,
            posted_at=match.group("date"),
            fields={
                "kind": "aggregated_median",
                "city_text": city,
                "property_type_text": property_type,
                "rent_price": _digits(match.group("price")),
                "range_low": _digits(match.group("low")),
                "range_high": _digits(match.group("high")),
                "sample_size": int(match.group("n")),
                "barometer_date": match.group("date"),
            },
            raw_text=match.group(0),
        )


class GelokaCollector(SourceCollector):
    NAME = "geloka"

    def collect(self, limit: int | None = None) -> Iterator[RawRecord]:
        emitted = 0
        for url in self.spec.urls:
            response = self.http.fetch(url)
            for record in parse_barometer(response.text, url):
                if limit is not None and emitted >= limit:
                    return
                yield record
                emitted += 1
