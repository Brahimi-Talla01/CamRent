"""Authentification de l'API interne : en-tête `Authorization: Bearer <jeton>`.

Pas de session, pas de cookie, donc pas de CSRF : un client (l'interface
d'administration 09b, un script d'exploitation) porte le jeton à chaque appel.
Un en-tête absent, d'un autre schéma ou vide ne donne aucun utilisateur ; le
refus (401) est produit par `permissions.require_action`.
"""

from __future__ import annotations

from django.http import HttpRequest

from .models import InternalUser
from .tokens import resolve_token

BEARER_SCHEME = "bearer"


def bearer_token(request: HttpRequest) -> str | None:
    """Jeton présenté par la requête, ou `None` si l'en-tête n'est pas exploitable."""
    header = request.headers.get("Authorization", "") or ""
    scheme, separator, value = header.partition(" ")
    if not separator or scheme.strip().lower() != BEARER_SCHEME:
        return None
    token = value.strip()
    return token or None


def authenticated_user(request: HttpRequest) -> InternalUser | None:
    """Compte porté par le jeton présenté, ou `None` s'il est inutilisable."""
    raw = bearer_token(request)
    if raw is None:
        return None
    return resolve_token(raw)
