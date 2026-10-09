"""Adaptateurs : convertissent une observation brute en *candidat* normalisable.

Chaque source a sa forme de Raw. L'adaptateur extrait les champs de source bruts
(ville, quartier, type, chambres, prix…) sans les résoudre : la résolution
canonique et la validation sont faites dans `silver.py`.

Sources gérées :

- ``koutchoumi`` (collecte live) : titre « <type> to rent at <ville>, <quartier> - <prix> »
  + slug ``/en/<id>/<slug>`` qui encode type/ville/quartier/pièces/prix ;
- ``reference_local`` : jeux locaux ``jumia.csv`` (``Address``, ``Designation``…) et
  ``koutchoumi1.csv`` (``Area = ville/quartier``, prix/chambres bornés ``> ``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .parsing import parse_price, parse_rooms


@dataclass
class Candidate:
    source: str
    source_listing_id: str
    source_file: str = ""
    url: str = ""
    city_raw: str = ""
    neighborhood_raw: str = ""
    property_type_raw: str = ""
    rent_price: int | None = None
    price_is_bound: bool = False
    bedrooms: int | None = None
    bedrooms_is_bound: bool = False
    bathrooms: int | None = None
    bathrooms_is_bound: bool = False
    area_m2: float | None = None
    furnished: str = ""
    parking: str = ""
    gated: str = ""
    posted_at: str | None = None
    collected_at: str | None = None
    extra: dict[str, object] = field(default_factory=dict)


_TITLE_RE = re.compile(
    r"(?i)^(?P<ptype>.+?)\s+to\s+rent\s+at\s+(?P<city>[^,]+),\s*(?P<nbhd>.+?)\s*-\s*(?P<price>.+)$"
)
_BEDROOM_RE = re.compile(r"(\d+)-bedroom")
_BATHROOM_RE = re.compile(r"(\d+)-bathroom")


def _adapt_koutchoumi_live(record: dict) -> Candidate:
    fields = record.get("fields") or {}
    title = str(fields.get("title") or "")
    slug = str(fields.get("slug") or "")

    city_raw = neighborhood_raw = property_type_raw = ""
    title_price = None
    match = _TITLE_RE.match(title)
    if match:
        property_type_raw = match.group("ptype").strip()
        city_raw = match.group("city").strip()
        neighborhood_raw = match.group("nbhd").strip()
        title_price = match.group("price").strip()

    if not property_type_raw and "-to-rent" in slug:
        property_type_raw = slug.split("-to-rent", 1)[0].replace("-", " ")
    if not city_raw:
        city_match = re.search(r"-to-rent-([a-z]+)-", slug)
        if city_match:
            city_raw = city_match.group(1)

    rent_price, price_is_bound = parse_price(fields.get("price_text") or title_price)

    bedrooms = _BEDROOM_RE.search(slug)
    bathrooms = _BATHROOM_RE.search(slug)

    return Candidate(
        source="koutchoumi",
        source_file="koutchoumi (live)",
        source_listing_id=record.get("source_listing_id", ""),
        url=record.get("url", ""),
        city_raw=city_raw,
        neighborhood_raw=neighborhood_raw,
        property_type_raw=property_type_raw,
        rent_price=rent_price,
        price_is_bound=price_is_bound,
        bedrooms=int(bedrooms.group(1)) if bedrooms else None,
        bathrooms=int(bathrooms.group(1)) if bathrooms else None,
        posted_at=record.get("posted_at"),
        collected_at=record.get("collected_at"),
    )


def _split_address(address: str) -> tuple[str, str]:
    parts = [part.strip() for part in (address or "").split(",") if part.strip()]
    if not parts:
        return "", ""
    city = parts[-2] if len(parts) >= 2 else parts[-1]
    return city, parts[0]


def _adapt_jumia(record: dict) -> Candidate:
    fields = record.get("fields") or {}
    city_raw, neighborhood_raw = _split_address(str(fields.get("Address") or ""))
    rent_price, price_is_bound = parse_price(fields.get("Price"))
    bedrooms, _ = parse_rooms(fields.get("Bedrooms"))
    bathrooms, _ = parse_rooms(fields.get("Bathrooms"))
    return Candidate(
        source="reference_local",
        source_file="jumia.csv",
        source_listing_id=record.get("source_listing_id", ""),
        url=record.get("url", ""),
        city_raw=city_raw,
        neighborhood_raw=neighborhood_raw,
        property_type_raw=str(fields.get("Designation") or ""),
        rent_price=rent_price,
        price_is_bound=price_is_bound,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        collected_at=record.get("collected_at"),
    )


def _split_area(area: str) -> tuple[str, str]:
    if "/" in area:
        city, neighborhood = area.split("/", 1)
        return city.strip(), neighborhood.strip()
    return area.strip(), ""


def _adapt_koutchoumi_file(record: dict) -> Candidate:
    fields = record.get("fields") or {}
    city_raw, neighborhood_raw = _split_area(str(fields.get("Area") or ""))
    rent_price, price_is_bound = parse_price(fields.get("Price"))
    bedrooms, bedrooms_bound = parse_rooms(fields.get("Bedrooms"))
    bathrooms, bathrooms_bound = parse_rooms(fields.get("Bathrooms"))
    return Candidate(
        source="reference_local",
        source_file="koutchoumi1.csv",
        source_listing_id=record.get("source_listing_id", ""),
        url=record.get("url", ""),
        city_raw=city_raw,
        neighborhood_raw=neighborhood_raw,
        property_type_raw=str(fields.get("Type") or ""),
        rent_price=rent_price,
        price_is_bound=price_is_bound,
        bedrooms=bedrooms,
        bedrooms_is_bound=bedrooms_bound,
        bathrooms=bathrooms,
        bathrooms_is_bound=bathrooms_bound,
        collected_at=record.get("collected_at"),
    )


def adapt(record: dict) -> Candidate | None:
    """Adapte une observation brute ; ``None`` si la source n'est pas gérée."""
    source = record.get("source")
    if source == "koutchoumi":
        return _adapt_koutchoumi_live(record)
    if source == "reference_local":
        source_file = str((record.get("fields") or {}).get("source_file") or "")
        if source_file == "jumia.csv":
            return _adapt_jumia(record)
        if source_file == "koutchoumi1.csv":
            return _adapt_koutchoumi_file(record)
    return None
