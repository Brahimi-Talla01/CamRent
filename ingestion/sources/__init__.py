"""Registre des collecteurs : nom de source → classe de collecteur."""

from __future__ import annotations

from .base import PageContext, SourceCollector
from .geloka import GelokaCollector
from .koutchoumi import KoutchoumiCollector
from .raw_document import RawDocumentCollector
from .reference_local import ReferenceLocalCollector

COLLECTORS: dict[str, type[SourceCollector]] = {
    "geloka": GelokaCollector,
    "koutchoumi": KoutchoumiCollector,
    "reference_local": ReferenceLocalCollector,
    "minfi_open_data": RawDocumentCollector,
    "ins_cameroon": RawDocumentCollector,
}

__all__ = ["COLLECTORS", "PageContext", "SourceCollector"]
