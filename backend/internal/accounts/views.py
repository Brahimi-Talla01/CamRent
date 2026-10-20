"""Vues HTTP de la session interne et des comptes (08b.1).

Les handlers restent fins (code-standards §API) : le parsing et la validation
sont dans `validation`, la lecture du jeton dans `authentication`, l'écriture du
journal dans `audit.service`. Chaque action sensible — connexion (succès et
échec), déconnexion, création de compte — produit une entrée d'audit.
"""

from __future__ import annotations

from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone

from ..audit.models import Outcome
from ..audit.service import record
from ..errors import (
    CONFLICT,
    INVALID_CREDENTIALS,
    InternalApiError,
    api_view,
    json_body,
    require_methods,
)
from .authentication import bearer_token
from .models import InternalUser
from .permissions import internal_user, require_action
from .roles import Action, Role
from .tokens import issue_token, revoke_token
from .validation import credentials

#: Cible des entrées de session : la ressource interne, jamais le mot de passe.
SESSION_TARGET = "internal-api/session"
INVALID_CREDENTIALS_MESSAGE = "Identifiants invalides."


def user_payload(user: InternalUser) -> dict[str, str]:
    """Forme publique d'un compte interne (jamais de secret, jamais de hachage)."""
    return {"email": user.email, "role": user.role}


@api_view
@require_methods("POST")
def login(request: HttpRequest) -> JsonResponse:
    """Échange e-mail + mot de passe contre un jeton d'accès.

    Un compte inconnu et un mot de passe faux produisent **la même** réponse
    (401 `invalid_credentials`, message générique) : pas d'énumération de comptes.
    """
    email, password = credentials(json_body(request))
    user = InternalUser.objects.filter(email__iexact=email, is_active=True).first()
    if user is None or not user.check_password(password):
        record(
            action=Action.SESSION_LOGIN.value,
            outcome=Outcome.FAILED,
            actor_email=email,
            target=SESSION_TARGET,
        )
        raise InternalApiError(401, INVALID_CREDENTIALS, INVALID_CREDENTIALS_MESSAGE)

    issued = issue_token(user)
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    record(
        action=Action.SESSION_LOGIN.value,
        outcome=Outcome.SUCCESS,
        actor=user,
        target=SESSION_TARGET,
    )
    response = JsonResponse(
        {
            "token": issued.token,
            "expires_at": issued.expires_at.isoformat(),
            "user": user_payload(user),
        }
    )
    # Un jeton ne doit jamais être mis en cache par un intermédiaire.
    response["Cache-Control"] = "no-store"
    return response


@api_view
@require_methods("POST")
@require_action(Action.SESSION_LOGOUT)
def logout(request: HttpRequest) -> HttpResponse:
    """Révoque le jeton présenté (204, sans corps)."""
    user = internal_user(request)
    raw = bearer_token(request)
    revoked = revoke_token(raw) if raw else False
    record(
        action=Action.SESSION_LOGOUT.value,
        outcome=Outcome.SUCCESS if revoked else Outcome.FAILED,
        actor=user,
        target=SESSION_TARGET,
    )
    return HttpResponse(status=204)


@api_view
@require_methods("GET")
@require_action(Action.SESSION_READ)
def me(request: HttpRequest) -> JsonResponse:
    """Compte porté par le jeton : adresse et rôle."""
    return JsonResponse({"user": user_payload(internal_user(request))})


@api_view
@require_methods("POST")
@require_action(Action.USERS_CREATE)
def create_user(request: HttpRequest) -> JsonResponse:
    """Crée un compte interne `admin` (action sensible, journalisée).

    Le rôle n'est pas un paramètre : `admin` est le seul rôle ouvert (ticket #61).
    Un second rôle s'ajouterait ici avec sa règle, pas par un champ libre.
    """
    actor = internal_user(request)
    email, password = credentials(json_body(request), enforce_policy=True)
    if InternalUser.objects.filter(email__iexact=email).exists():
        raise InternalApiError(
            409, CONFLICT, "Un compte interne existe déjà pour cette adresse."
        )
    try:
        user = InternalUser.objects.create_user(
            email=email, password=password, role=Role.ADMIN
        )
    except IntegrityError:
        raise InternalApiError(
            409, CONFLICT, "Un compte interne existe déjà pour cette adresse."
        ) from None

    record(
        action=Action.USERS_CREATE.value,
        outcome=Outcome.SUCCESS,
        actor=actor,
        target=f"internal-user:{user.email}",
        details={"role": user.role},
    )
    response = JsonResponse({"user": user_payload(user)}, status=201)
    response["Cache-Control"] = "no-store"
    return response
