"""Lecture de la chaîne de connexion PostgreSQL pour l'API interne.

Django ne sait pas lire une URL de connexion : on la convertit ici, dans un
module **pur** (aucun import de `django.conf.settings`), pour que la
conversion soit testable sans base ni application démarrée.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

POSTGRES_SCHEMES = frozenset({"postgres", "postgresql", "postgresql+psycopg"})


def from_url(url: str) -> dict[str, Any]:
    """Convertit `postgresql://…` en dictionnaire `DATABASES["default"]`.

    Raises:
        ImproperlyConfigured: si l'URL est vide, n'est pas PostgreSQL ou ne nomme
            pas de base. Le message ne reprend **jamais** d'identifiant ni de mot
            de passe : il décrit seulement ce qui manque (AGENTS.md §9).
    """
    if not url.strip():
        raise ImproperlyConfigured("L'URL de connexion à la base est vide.")
    parsed = urlparse(url.strip())
    if parsed.scheme not in POSTGRES_SCHEMES:
        raise ImproperlyConfigured(
            "L'API interne attend une URL PostgreSQL "
            "(postgresql://<utilisateur>:<mot de passe>@<hôte>:<port>/<base>)."
        )
    name = parsed.path.lstrip("/")
    if not name:
        raise ImproperlyConfigured("L'URL PostgreSQL de l'API interne ne nomme aucune base.")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
        "CONN_MAX_AGE": 60,
    }
