"""Point d'entrée WSGI de l'API interne (`gunicorn backend.internal.wsgi`)."""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.internal.settings")

application = get_wsgi_application()
