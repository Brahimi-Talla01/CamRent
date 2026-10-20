"""Réglages communs de l'API interne (aucune valeur d'environnement ici).

Ce module ne dépend **d'aucune variable d'environnement** : il porte la
structure (applications, middlewares, modèle d'utilisateur, journalisation) que
partagent les réglages réels (`settings.py`) et les réglages de test
(`settings_test.py`). Aucun secret n'y figure.
"""

from __future__ import annotations

from pathlib import Path

from . import config

# Racine du dépôt : `backend/internal/settings_base.py` → parents[2].
BASE_DIR = Path(__file__).resolve().parents[2]

INSTALLED_APPS = [
    # Pas de `django.contrib.auth` ni de `django.contrib.admin` : le socle
    # interne porte son propre modèle de compte et son propre contrôle d'accès
    # (rôle + action), sans permissions Django ni interface d'administration.
    "backend.internal.accounts",
    "backend.internal.audit",
]

# Pas de middleware applicatif : les refus prévus sont interceptés par le
# décorateur `errors.api_view` (Django convertit les exceptions en 500 avant le
# middleware), et les routes inconnues passent par `handler404`.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "backend.internal.urls"
WSGI_APPLICATION = "backend.internal.wsgi.application"
ASGI_APPLICATION = "backend.internal.asgi.application"

TEMPLATES: list[dict[str, object]] = []

AUTH_USER_MODEL = "accounts.InternalUser"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "fr-fr"

# L'API n'a pas de session ni de cookie : l'authentification est un jeton
# `Authorization: Bearer`, donc il n'y a ni session, ni CSRF, ni redirection
# de barre oblique finale (une route interne est un contrat exact).
APPEND_SLASH = False

# Réglages propres au socle interne (surchargés par `settings.py` depuis
# l'environnement quand cela a du sens).
INTERNAL_TOKEN_TTL_HOURS = config.DEFAULT_TOKEN_TTL_HOURS
INTERNAL_MIN_PASSWORD_LENGTH = config.MIN_PASSWORD_LENGTH
INTERNAL_API_VERSION = config.API_VERSION

# Journalisation : sortie standard, sans contenu de requête. Le nom du logger
# `backend.internal` regroupe les erreurs de l'application interne.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "backend.internal": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
