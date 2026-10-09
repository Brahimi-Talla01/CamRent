"""Base abstraite des collecteurs d'ingestion.

Un collecteur :

- vérifie la **porte légale** : une source non confirmée refuse de tourner sans
  ``--confirm-legal`` (invariant AGENTS.md) ;
- produit des ``RawRecord`` **bruts**, sans normalisation (Phase 2) ;
- respecte le débit et ``robots.txt`` via ``HttpClient``.

``PageContext.iter_detail`` borne le nombre de fetchs de détail par page pour ne
pas surcharger la source : au-delà du budget, les liens restants sont ignorés et
journalisés.
"""

from __future__ import annotations

import abc
import logging
import re
from collections.abc import Iterable, Iterator

from .. import config
from ..http_client import HttpClient, LegalGateError
from ..models import RawRecord

logger = logging.getLogger("camrent.ingestion.source")

_ID_RE = re.compile(r"\d+")


def extract_numeric_id(candidate: str, prefix: str = "") -> str:
    """Extrait un identifiant numérique d'un fragment (URL, href…)."""
    match = _ID_RE.search(candidate)
    if not match:
        raise ValueError(f"aucun identifiant numérique trouvé dans {candidate!r}")
    return f"{prefix}{match.group(0)}"


class SourceCollector(abc.ABC):
    """Contrat commun à toutes les sources."""

    NAME: str = "abstract"

    def __init__(
        self,
        spec: config.SourceSpec,
        http: HttpClient | None = None,
        confirm_legal: str | None = None,
    ) -> None:
        self.spec = spec
        self.confirm_legal = confirm_legal
        self._http = http

        if spec.requires_confirm and not confirm_legal:
            raise LegalGateError(
                f"La source '{spec.name}' est de droits '{spec.rights}'. "
                f"Fournis --confirm-legal \"<phrase d'avertissement>\" après avoir vérifié "
                f"robots.txt et les CGU. {spec.rights_notice}"
            )

    @property
    def http(self) -> HttpClient:
        if self._http is None:
            self._http = HttpClient()
        return self._http

    @abc.abstractmethod
    def collect(self, limit: int | None = None) -> Iterator[RawRecord]:
        """Produit les observations brutes ; `limit` borne le nombre d'observations."""


class PageContext:
    """Services offerts au parsing d'une page : budget de fetchs de détail."""

    def __init__(self, http: HttpClient, page_url: str, budget: int | None = None) -> None:
        self.http = http
        self.page_url = page_url
        self.budget = config.DETAIL_BUDGET_PER_PAGE if budget is None else budget
        self.used = 0
        self.skipped: list[str] = []

    def iter_detail(self, urls: Iterable[str]) -> Iterator[tuple[str, str]]:
        """Yield ``(url, html)`` pour les fetchs de détail, dans la limite du budget."""
        for url in urls:
            if self.used >= self.budget:
                self.skipped.append(url)
                continue
            self.used += 1
            try:
                yield url, self.http.fetch(url).text
            except Exception as error:  # un détail qui échoue n'arrête pas la page
                logger.warning("détail inaccessible %s : %s", url, error)

        if self.skipped:
            logger.info(
                "budget de détail atteint sur %s : %d lien(s) ignoré(s)", self.page_url,
                len(self.skipped),
            )
