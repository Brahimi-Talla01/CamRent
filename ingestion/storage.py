"""Stockage : JSONL brut daté et immuable + métadonnées de lot.

Layout conforme à la spec Phase 1 §2 :

    data/raw/
    ├── listings/<YYYY-MM-DD>/<source>_<HHMMSS>.jsonl
    ├── reference_data/<YYYY-MM-DD>/<source>_<HHMMSS>.jsonl
    ├── user_submissions/<YYYY-MM-DD>/...
    └── metadata/<YYYY-MM-DD>/<source>_<HHMMSS>.json   (un fichier par lot)

Invariant : le brut n'est **jamais** écrasé. Chaque run crée un fichier horodaté ;
relancer une collecte ne corrompt donc pas les données existantes (idempotence).
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from . import config
from .models import RawRecord, now_iso


def _utc_day() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")


def _utc_stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%H%M%S")


def raw_dir(category: str, day: str | None = None) -> Path:
    """``data/raw/<category>/<YYYY-MM-DD>/`` (créé si absent)."""
    path = config.RAW_ROOT / category / (day or _utc_day())
    path.mkdir(parents=True, exist_ok=True)
    return path


class RawJsonlWriter:
    """Écrit le brut **au fil de la collecte** (une ligne JSON par observation).

    Un run interrompu conserve tout ce qui a déjà été écrit. Si rien n'a été
    collecté, ``close()``/``abort()`` supprime le fichier vide : aucun artefact
    trompeur n'est laissé derrière.
    """

    def __init__(
        self,
        *,
        category: str,
        source: str,
        day: str | None = None,
        stamp: str | None = None,
    ) -> None:
        self.category = category
        self.source = source
        self.day = day or _utc_day()
        self.stamp = stamp or _utc_stamp()
        self.path = raw_dir(category, self.day) / f"{source}_{self.stamp}.jsonl"
        self._handle = self.path.open("w", encoding="utf-8")
        self.count = 0
        self._closed = False

    def write(self, record: RawRecord) -> None:
        self._handle.write(
            json.dumps(record.to_dict(), ensure_ascii=False, default=str) + "\n"
        )
        self._handle.flush()
        self.count += 1

    def abort(self) -> None:
        """Ferme et supprime le fichier vide (aucun enregistrement écrit)."""
        self.close()
        if self.count == 0 and self.path.exists():
            self.path.unlink()

    def close(self) -> None:
        if not self._closed:
            self._handle.close()
            self._closed = True

    def __enter__(self) -> RawJsonlWriter:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.abort()


def write_metadata(
    spec: config.SourceSpec,
    writer: RawJsonlWriter,
    urls: list[str],
    notes: str = "",
) -> Path:
    """Écrit les métadonnées du lot : source, URL, date, méthode, volume, format."""
    path = raw_dir(config.CATEGORY_METADATA, writer.day) / f"{spec.name}_{writer.stamp}.json"
    payload: dict[str, Any] = {
        "source": spec.name,
        "category": writer.category,
        "method": spec.method,
        "format": "jsonl",
        "collected_at": now_iso(),
        "collected_day": writer.day,
        "record_count": writer.count,
        "raw_file": str(writer.path.relative_to(config.RAW_ROOT)),
        "urls": urls,
        "rights_status": spec.rights,
        "rights_notice": spec.rights_notice,
        "notes": notes,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


def iter_raw_files() -> Iterator[Path]:
    """Itère sur les fichiers brut JSONL (hors métadonnées)."""
    for category in config.STORAGE_CATEGORIES:
        category_dir = config.RAW_ROOT / category
        if not category_dir.exists():
            continue
        yield from sorted(category_dir.glob("*/*.jsonl"))


def iter_metadata_files() -> Iterator[Path]:
    meta_dir = config.RAW_ROOT / config.CATEGORY_METADATA
    if not meta_dir.exists():
        return
    yield from sorted(meta_dir.glob("*/*.json"))
