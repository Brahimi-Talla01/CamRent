"""Contrôle d'accès de l'API interne : authentification puis autorisation.

Deux refus distincts, tous deux testés :

- **401 `unauthenticated`** — aucun compte ne peut être identifié (jeton absent,
  mal formé, inconnu, expiré ou révoqué). Aucune écriture d'audit : l'auteur est
  inconnu et un appelant anonyme ne doit pas pouvoir remplir le journal.
- **403 `forbidden`** — le compte est identifié mais son rôle n'ouvre pas
  l'action. L'auteur étant connu, le refus est **journalisé** (outcome `denied`).

Chaque vue déclare l'action qu'elle protège ; aucune route interne n'est
protégée « par défaut ».
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest

from ..audit.models import Outcome
from ..audit.service import record
from ..errors import UNAUTHENTICATED, InternalApiError, field_error
from .authentication import authenticated_user
from .models import InternalUser
from .roles import Action


def internal_user(request: HttpRequest) -> InternalUser:
    """Compte authentifié posé par `require_action` (pour les vues protégées)."""
    user: InternalUser | None = getattr(request, "internal_user", None)
    if user is None:  # pragma: no cover - garde-fou : décorateur obligatoire
        raise InternalApiError(401, UNAUTHENTICATED, "Authentification requise.")
    return user


def require_action(action: Action) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Exige un compte authentifié dont le rôle ouvre `action`."""

    def decorator(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            user = authenticated_user(request)
            if user is None:
                raise InternalApiError(
                    401,
                    UNAUTHENTICATED,
                    "Authentification requise.",
                    [field_error("Authorization", "Jeton Bearer requis, valide et non expiré.")],
                )
            if not user.can_perform(action):
                record(
                    action=action.value,
                    outcome=Outcome.DENIED,
                    actor=user,
                    target=request.path,
                    details={"method": request.method, "role": user.role},
                )
                raise InternalApiError(403, "forbidden", "Accès refusé pour ce rôle.")
            request.internal_user = user
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
