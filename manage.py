#!/usr/bin/env python
"""Gestion de l'API interne Django (08b.1).

Exemples :

    python manage.py migrate                       # crée les tables comptes + audit
    python manage.py create_internal_user --email admin@camrent.local
    uvicorn backend.internal.asgi:application --port 8001

Le module de réglages est surchargeable pour les tests :
`DJANGO_SETTINGS_MODULE=backend.internal.settings_test python manage.py ...`.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    """Exécute une commande de gestion Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.internal.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover - dépendance d'environnement
        raise SystemExit(
            "Django est introuvable : installez l'extra `internal` "
            "(pip install -e '.[internal]')."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
