"""Point d'entrée de l'API interne Django (08b.1).

Ce projet sert **uniquement** les routes internes, sous `/internal/api/v1`. Il
ne monte aucune route publique : l'estimation, le marché et la comparaison sont
servies par l'application FastAPI (`backend/api/app.py`), qui n'expose à son
tour aucune route interne (spec 08 §Scope Limits, ticket #61).
"""

from __future__ import annotations

from django.urls import path

from . import config
from .accounts import views as accounts_views
from .audit import views as audit_views
from .health import health

# Django attend des chemins **relatifs** : le préfixe versionné est retiré du
# `/` initial. Une route n'existe donc pas hors `/internal/api/v1`.
_PREFIX = config.API_PREFIX.strip("/")

urlpatterns = [
    # Santé : seule route sans authentification, pour vérifier que le service
    # répond avant de disposer d'un compte (même rôle que `/api/v1/health`).
    path(f"{_PREFIX}/health", health, name="internal-health"),
    # Session interne.
    path(f"{_PREFIX}/auth/login", accounts_views.login, name="internal-login"),
    path(f"{_PREFIX}/auth/logout", accounts_views.logout, name="internal-logout"),
    path(f"{_PREFIX}/me", accounts_views.me, name="internal-me"),
    # Comptes internes (action sensible, journalisée).
    path(f"{_PREFIX}/users", accounts_views.create_user, name="internal-users"),
    # Journal d'audit (consultable, réservé au rôle admin).
    path(f"{_PREFIX}/audit", audit_views.entries, name="internal-audit"),
]

handler400 = "backend.internal.errors.bad_request"
handler404 = "backend.internal.errors.not_found"
handler500 = "backend.internal.errors.server_error"
