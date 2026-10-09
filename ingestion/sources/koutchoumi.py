"""Koutchoumi — annonces détaillées (catégorie `listings`).

La source n'a **pas de CGU publiée** (vérifié le 2026-10-09) et son ``robots.txt``
ne contient aucune règle active : la collecte est donc soumise à ``--confirm-legal``
et applique un débit limité, un User-Agent transparent et aucune donnée personnelle.

Structure réelle observée (2026-10-09) :

- pages de **catégorie** : ``/<type>-to-rent-at-<city>-cameroon.html`` (+ ``?page=N``) ;
- pages de **détail**     : ``/en/<id>/<slug>`` — le slug encode ville, quartier,
  pièces et prix.

Phase 1 = capture brute : on conserve l'URL, l'identifiant de source et les valeurs
de source **non normalisées** ; la mise au schéma cible relève de la Phase 2.

Minimisation des données (AGENTS.md §9) : on **ne stocke aucune donnée
personnelle**. Les pages de détail contiennent des téléphones, e-mails et noms
d'annonceurs ; on n'en conserve donc **pas** le texte brut — seuls l'URL, le slug
(qui encode ville/quartier/type/pièces/prix) et les champs structurés sont gardés.
"""

from __future__ import annotations

import os
import re
import urllib.parse
from collections.abc import Iterator
from html.parser import HTMLParser

from ..models import RawRecord
from .base import PageContext, SourceCollector

BASE_URL = "https://www.koutchoumi.com"

CITY_SLUGS = ("douala", "yaounde")
RENT_TYPES = ("studios", "apartments", "houses", "offices", "shops", "stores", "warehouses")

# Bornage du débit : nombre de pages de catégorie parcourues au plus.
MAX_PAGES_PER_CATEGORY = int(os.environ.get("CAMRENT_KOUTCHOUMI_MAX_PAGES", "1"))

_DETAIL_HREF_RE = re.compile(r"/(?:en|fr)/\d+/")
_LISTING_ID_RE = re.compile(r"/(?:en|fr)/(\d+)(?:/|$)")
_PRICE_RE = re.compile(r"(?i)([>\u2265]?\s*\d[\d\s\u00a0.,]*\s*(?:FCFA|CFA))")
_SLUG_PRICE_RE = re.compile(r"(\d[\d\-]*)-fcfa", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\b")

# Libellés de champs possibles (FR/EN), tels qu'affichés par la source.
_LABELS: dict[str, tuple[str, ...]] = {
    "city_text": ("City", "Ville"),
    "neighborhood_text": ("Quartier", "Neighborhood", "Localisation", "Location"),
    "property_type_text": ("Type", "Property type", "Type de bien"),
    "bedrooms_text": ("Bedrooms", "Chambres", "Rooms"),
    "bathrooms_text": ("Bathrooms", "Salles de bain", "Salle de bain"),
    "area_text": ("Surface", "Area", "Superficie"),
    "furnished_text": ("Furnished", "Meublé", "Meuble"),
}


def category_urls() -> list[str]:
    """URLs des pages de catégorie (location) pour Douala et Yaoundé."""
    return [
        f"{BASE_URL}/{rent_type}-to-rent-at-{city}-cameroon.html"
        for rent_type in RENT_TYPES
        for city in CITY_SLUGS
    ]


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        if _DETAIL_HREF_RE.search(href):
            self.links.append(urllib.parse.urljoin(BASE_URL, href))


class _TextParser(HTMLParser):
    """Texte visible, en ignorant le contenu de ``<script>``/``<style>``."""

    _SKIP_TAGS = ("script", "style", "noscript")

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = " ".join(data.split())
        if text:
            self.lines.append(text)


def _extract_text(html: str) -> str:
    parser = _TextParser()
    parser.feed(html)
    return "\n".join(parser.lines)


def detail_links(html: str) -> list[str]:
    """Liens de détail (dédupliqués, ordre d'apparition conservé)."""
    parser = _AnchorParser()
    parser.feed(html)
    return list(dict.fromkeys(parser.links))


def _extract_labeled(text: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        match = re.search(rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*(.+?)\s*$", text)
        if match:
            return " ".join(match.group(1).split())
    return None


def _price_from_slug(url: str) -> str | None:
    match = _SLUG_PRICE_RE.search(url)
    if not match:
        return None
    return match.group(1).replace("-", " ") + " FCFA"


def parse_detail(url: str, html: str) -> RawRecord | None:
    """Extrait une observation brute d'une page de détail (sans réseau → testable)."""
    match = _LISTING_ID_RE.search(url)
    if not match:
        return None
    listing_id = match.group(1)

    text = _extract_text(html)
    slug = url.rstrip("/").rsplit("/", 1)[-1]

    price_match = _PRICE_RE.search(text)
    price_text = _price_from_slug(url) or (
        " ".join(price_match.group(1).split()) if price_match else None
    )

    fields: dict[str, str | None] = {
        "slug": slug,
        "title": text.split("\n", 1)[0][:200] if text else None,
        "price_text": price_text,
    }
    for field, labels in _LABELS.items():
        value = _extract_labeled(text, labels)
        if value is not None:
            fields[field] = value

    date_match = _DATE_RE.search(text)
    posted_at = date_match.group(1) if date_match else None

    # raw_text volontairement vide : la page contient des données personnelles.
    return RawRecord(
        source="koutchoumi",
        source_listing_id=listing_id,
        url=url,
        posted_at=posted_at,
        fields=fields,
    )


class KoutchoumiCollector(SourceCollector):
    NAME = "koutchoumi"

    def collect(self, limit: int | None = None) -> Iterator[RawRecord]:
        emitted = 0
        seen_ids: set[str] = set()

        for category_url in category_urls():
            for page in range(1, MAX_PAGES_PER_CATEGORY + 1):
                if limit is not None and emitted >= limit:
                    return

                page_url = (
                    category_url if page == 1 else f"{category_url}?page={page}"
                )
                response = self.http.fetch(page_url)

                links = [
                    link
                    for link in detail_links(response.text)
                    if self._id_of(link) not in seen_ids
                ]
                if not links:
                    break

                context = PageContext(self.http, page_url)
                for detail_url, detail_html in context.iter_detail(links):
                    record = parse_detail(detail_url, detail_html)
                    if record is None or record.source_listing_id in seen_ids:
                        continue
                    seen_ids.add(record.source_listing_id)
                    yield record
                    emitted += 1
                    if limit is not None and emitted >= limit:
                        return

    @staticmethod
    def _id_of(url: str) -> str | None:
        match = _LISTING_ID_RE.search(url)
        return match.group(1) if match else None
