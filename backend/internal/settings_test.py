"""Réglages de test de l'API interne : aucune base ni secret requis.

La suite unitaire doit rester exécutable **sans PostgreSQL** et sans variable
d'environnement, comme le reste du dépôt. Les tests de l'API interne tournent
donc sur SQLite en mémoire (mêmes migrations, mêmes modèles) ; les réglages
réels (`settings.py`) exigent, eux, PostgreSQL et une clé explicite.

La clé ci-dessous est **factice** et réservée aux tests : elle n'ouvre aucun
accès et n'est pas un secret (elle ne protège aucune donnée réelle).
"""

from __future__ import annotations

from . import config
from .settings_base import *  # noqa: F401,F403 - réglages communs

SECRET_KEY = "test-only-key-for-camrent-internal-api-never-used-outside-tests-0000"
DEBUG = False
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Hachage rapide : les tests ne mesurent pas la robustesse du hachage de mot de
# passe (PBKDF2 reste celui des réglages réels), seulement les règles d'accès.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

INTERNAL_TOKEN_TTL_HOURS = config.DEFAULT_TOKEN_TTL_HOURS
