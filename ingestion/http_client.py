"""Client HTTP respectueux, fondé sur ``requests``.

Garanties appliquées à chaque requête :

- **robots.txt** vérifié automatiquement par hôte (``urllib.robotparser``) ;
- **débit limité** par hôte (token bucket) pour ne pas charger la source ;
- **User-Agent transparent** identifiant la recherche et un contact ;
- **retries** avec repli exponentiel sur erreurs réseau ;
- **porte légale** (`LegalGateError`) levée en amont par les collecteurs dont les
  droits ne sont pas confirmés.

Aucune donnée n'est parsée ici : le client ne fait que rapporter le contenu brut.
"""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass

import requests

from . import config
from .models import now_iso

logger = logging.getLogger("camrent.ingestion.http")


class RobotsDisallowed(RuntimeError):
    """robots.txt interdit la ressource demandée."""


class LegalGateError(RuntimeError):
    """La source exige une confirmation légale explicite qui n'a pas été fournie."""


@dataclass
class FetchResult:
    url: str
    status: int
    text: str
    content_type: str
    fetched_at: str

    def is_html(self) -> bool:
        return "html" in self.content_type.lower() or self.text.lstrip().lower().startswith(
            ("<!doctype", "<html")
        )


class TokenBucket:
    """Limiteur de débit minimal : un délai minimal entre requêtes d'un même hôte."""

    def __init__(self, interval_seconds: float) -> None:
        self._interval = interval_seconds
        self._last: dict[str, float] = {}

    def wait(self, host: str) -> None:
        now = time.monotonic()
        elapsed = now - self._last.get(host, 0.0)
        if elapsed < self._interval:
            time.sleep(self._interval - elapsed)
        self._last[host] = time.monotonic()


class RobotsCache:
    """Vérification de robots.txt par hôte, mise en cache.

    Politique prudente : si robots.txt est **inaccessible**, on refuse la collecte
    (on ne suppose pas l'autorisation).
    """

    def __init__(self) -> None:
        self._cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def can_fetch(self, url: str, user_agent: str) -> bool:
        parsed = urllib.parse.urlsplit(url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        if host not in self._cache:
            robots_url = urllib.parse.urljoin(host, "/robots.txt")
            parser = urllib.robotparser.RobotFileParser()
            try:
                with urllib.request.urlopen(
                    robots_url, timeout=config.REQUEST_TIMEOUT
                ) as response:
                    parser.parse(
                        response.read().decode("utf-8", errors="replace").splitlines()
                    )
                self._cache[host] = parser
            except (urllib.error.URLError, OSError):
                logger.warning(
                    "robots.txt inaccessible pour %s : collecte refusée par prudence", host
                )
                self._cache[host] = None
        entry = self._cache[host]
        if entry is None:
            return False
        return entry.can_fetch(user_agent, url)


class HttpClient:
    """Client partagé : robots.txt + débit + retries, une session ``requests``."""

    def __init__(self, user_agent: str | None = None) -> None:
        self.user_agent = user_agent or config.USER_AGENT
        self._bucket = TokenBucket(config.RATE_LIMIT_SECONDS)
        self._robots = RobotsCache()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.user_agent})

    def fetch(self, url: str, *, respect_robots: bool = True) -> FetchResult:
        """GET respectueux ; lève ``RobotsDisallowed`` si la ressource est interdite."""
        if respect_robots and not self._robots.can_fetch(url, self.user_agent):
            raise RobotsDisallowed(f"robots.txt interdit {url}")

        self._bucket.wait(urllib.parse.urlsplit(url).netloc)

        attempts = config.MAX_RETRIES + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self._session.get(url, timeout=config.REQUEST_TIMEOUT)
                response.raise_for_status()
                return FetchResult(
                    url=url,
                    status=response.status_code,
                    text=response.text,
                    content_type=response.headers.get("Content-Type", ""),
                    fetched_at=now_iso(),
                )
            except (requests.RequestException, OSError) as error:
                last_error = error
                if attempt < attempts - 1:
                    backoff = config.RETRY_BACKOFF_SECONDS * (attempt + 1)
                    logger.warning(
                        "échec fetch %s (tentative %d/%d) : %s → retry dans %.0fs",
                        url,
                        attempt + 1,
                        attempts,
                        error,
                        backoff,
                    )
                    time.sleep(backoff)
        raise RuntimeError(f"fetch échoué après {attempts} tentatives : {url}") from last_error
