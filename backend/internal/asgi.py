"""Point d'entrée ASGI de l'API interne (`uvicorn backend.internal.asgi:application`).

Application **distincte** de l'API publique : `uvicorn backend.api.app:app`
sert le public, `uvicorn backend.internal.asgi:application` sert l'interne.
Aucune des deux ne monte les routes de l'autre (ticket #61).
"""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.internal.settings")

application = get_asgi_application()
