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
import hashlib
import json
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from . import config
from .models import RawRecord, now_iso

# Taille de lecture pour le calcul d'empreinte (le brut peut être volumineux :
# on hashe en flux, sans charger le fichier entier en mémoire).
_HASH_CHUNK_BYTES = 65536


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


def content_digest(path: Path) -> tuple[str, int]:
    """Empreinte SHA-256 du fichier brut et sa taille en octets.

    L'empreinte porte sur le **contenu écrit**, octet pour octet : elle permet de
    constater qu'un lot n'a pas été altéré après collecte (raw immuable) et
    d'alimenter la traçabilité de provenance (plan de réalignement §7.7).
    """
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(_HASH_CHUNK_BYTES):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def write_metadata(
    spec: config.SourceSpec,
    writer: RawJsonlWriter,
    urls: list[str],
    notes: str = "",
    *,
    validation_status: str = "not_run",
    validation_failures: Sequence[str] = (),
) -> Path:
    """Écrit les métadonnées du lot (provenance, volume, empreinte, validation).

    Le fichier de métadonnées est écrit **une seule fois**, à la fin de la
    collecte, comme le brut : il n'est jamais réécrit ensuite (invariant raw).
    Le statut de validation consigné ici est celui des contrôles Bronze
    évaluables **à la collecte** (existence, format, volume, clés requises). La
    validation Bronze complète, qui exige les métadonnées, se fait via
    ``python -m ingestion --validate-bronze``.
    """
    sha256, size_bytes = content_digest(writer.path)
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
        # Provenance renforcée (spec Phase 1 §6) : version du code de collecte
        # et de parsing, empreinte de contenu du lot, statut de validation.
        "connector_version": config.CONNECTOR_VERSION,
        "content_bytes": size_bytes,
        "content_sha256": sha256,
        "lot_validation_status": validation_status,
        "lot_validation_failures": list(validation_failures),
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
    """Itère sur les métadonnées de lot, du plus ancien au plus récent.

    Le tri porte sur le chemin complet (date puis horodatage du lot).
    """
    meta_dir = config.RAW_ROOT / config.CATEGORY_METADATA
    if not meta_dir.exists():
        return
    yield from sorted(meta_dir.glob("*/*.json"))
