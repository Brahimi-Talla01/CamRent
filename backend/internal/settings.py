"""Réglages réels de l'API interne : tout vient de l'environnement.

Aucun secret, aucun identifiant et aucun chemin de base en dur (AGENTS.md §3
et §9). Deux variables sont **obligatoires** ; leur absence lève une erreur
explicite qui **nomme la variable**, sans jamais reprendre d'identifiant :

- `INTERNAL_SECRET_KEY` — clé de signature Django (`python -c "import secrets;
  print(secrets.token_urlsafe(50))"`) ;
- `DATABASE_URL` — base applicative PostgreSQL, la même que `pipelines`, `ml` et
  l'API publique.

Variables facultatives : `INTERNAL_DEBUG` (`1` en développement seulement),
`INTERNAL_ALLOWED_HOSTS` (liste séparée par des virgules),
`INTERNAL_TOKEN_TTL_HOURS` (durée de vie d'un jeton, défaut 12 h).
"""

from __future__ import annotations

import os

from django.core.exceptions import ImproperlyConfigured

from . import config, database
from .settings_base import *  # noqa: F401,F403 - réglages communs

SECRET_KEY_ENV = "INTERNAL_SECRET_KEY"
DATABASE_URL_ENV = "DATABASE_URL"
DEBUG_ENV = "INTERNAL_DEBUG"
ALLOWED_HOSTS_ENV = "INTERNAL_ALLOWED_HOSTS"
TOKEN_TTL_ENV = "INTERNAL_TOKEN_TTL_HOURS"


def _required(name: str) -> str:
    """Variable d'environnement obligatoire, ou erreur nommant la variable."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(
            f"{name} est requise pour démarrer l'API interne. "
            "Voir `.env.example` : aucun secret n'est écrit dans le code."
        )
    return value


def _token_ttl_hours() -> int:
    """Durée de vie d'un jeton, entière et strictement positive."""
    raw = os.environ.get(TOKEN_TTL_ENV, "").strip()
    if not raw:
        return config.DEFAULT_TOKEN_TTL_HOURS
    try:
        hours = int(raw)
    except ValueError:
        hours = 0
    if hours <= 0:
        raise ImproperlyConfigured(
            f"{TOKEN_TTL_ENV} doit être un entier strictement positif (heures)."
        )
    return hours


SECRET_KEY = _required(SECRET_KEY_ENV)
DEBUG = os.environ.get(DEBUG_ENV, "").strip().lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(ALLOWED_HOSTS_ENV, "localhost,127.0.0.1").split(",")
    if host.strip()
]
DATABASES = {"default": database.from_url(_required(DATABASE_URL_ENV))}
INTERNAL_TOKEN_TTL_HOURS = _token_ttl_hours()

# L'API interne ne sert que du JSON : pas de formulaire, pas de fichier statique.
DATA_UPLOAD_MAX_MEMORY_SIZE = 256 * 1024
