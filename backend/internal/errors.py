"""Erreurs de l'API interne : le **même format** que l'API publique.

Toutes les erreurs sortent sous la forme `{"error": {"code", "message",
"details"}}` (comparer `backend/api/errors.py`), pour qu'un client interne
n'ait qu'un seul format à traiter. Aucune trace technique n'est renvoyée : un
échec interne est **générique** et seul le type de l'exception est journalisé
(AGENTS.md §9), jamais son message ni la charge utile.

Codes stables exposés :

- `validation_error` (422) — l'entrée ne respecte pas le contrat ;
- `bad_request` (400) — corps mal formé mais comprise ;
- `unauthenticated` (401) — jeton absent, invalide, expiré ou révoqué ;
- `invalid_credentials` (401) — couple e-mail / mot de passe refusé ;
- `forbidden` (403) — authentifié, mais le rôle n'accorde pas l'action ;
- `not_found` (404) — route ou ressource inconnue ;
- `method_not_allowed` (405) — méthode absente pour cette route ;
- `conflict` (409) — la ressource existe déjà (compte interne) ;
- `internal_error` (500) — échec interne, message générique.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)

VALIDATION_ERROR = "validation_error"
BAD_REQUEST = "bad_request"
UNAUTHENTICATED = "unauthenticated"
INVALID_CREDENTIALS = "invalid_credentials"
FORBIDDEN = "forbidden"
NOT_FOUND = "not_found"
METHOD_NOT_ALLOWED = "method_not_allowed"
CONFLICT = "conflict"
INTERNAL_ERROR = "internal_error"

INTERNAL_ERROR_MESSAGE = "Erreur interne du service."


class InternalApiError(Exception):
    """Refus prévu de l'API interne, transformé en réponse au format unique."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> JsonResponse:
    """Construit une réponse d'erreur au format unique de l'API."""
    return JsonResponse(
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            }
        },
        status=status_code,
    )


def field_error(field: str, message: str) -> dict[str, str]:
    """Un détail d'erreur, ciblant un champ précis."""
    return {"field": field, "message": message}


def validation_error(
    details: list[dict[str, str]],
    message: str = "Entrée invalide.",
) -> InternalApiError:
    """Refus de contrat (422) avec le détail par champ."""
    return InternalApiError(422, VALIDATION_ERROR, message, details)


def json_body(request: HttpRequest) -> dict[str, Any]:
    """Lit le corps JSON de la requête, qui doit être un objet.

    Un corps absent ou non-objet est un refus de contrat (422) ; un JSON
    syntaxiquement invalide est une requête mal formée (400).
    """
    if not request.body:
        raise validation_error([field_error("body", "Corps JSON requis.")])
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise InternalApiError(400, BAD_REQUEST, "Corps JSON mal formé.") from None
    if not isinstance(payload, dict):
        raise validation_error([field_error("body", "Un objet JSON est attendu.")])
    return payload


def api_view(view: Callable[..., Any]) -> Callable[..., Any]:
    """Traduit un refus prévu (`InternalApiError`) en réponse au format unique.

    Un middleware ne suffirait pas : Django convertit désormais toute exception
    non gérée en réponse 500 **avant** d'atteindre le middleware applicatif, ce
    qui transformerait un refus prévu (401, 422) en erreur interne. Le refus est
    donc intercepté au plus près de la vue ; un échec inattendu reste couvert
    par `handler500`, dont le message est générique.
    """

    @wraps(view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        try:
            return view(request, *args, **kwargs)
        except InternalApiError as exc:
            return error_response(exc.status_code, exc.code, exc.message, exc.details)

    return wrapper


def require_methods(*allowed: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Réserve une vue aux méthodes listées ; sinon 405 au format unique."""

    def decorator(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            if request.method not in allowed:
                raise InternalApiError(
                    405,
                    METHOD_NOT_ALLOWED,
                    f"Méthode {request.method} non autorisée pour cette route.",
                )
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def _json_404(details: list[dict[str, str]] | None = None) -> JsonResponse:
    return error_response(404, NOT_FOUND, "Ressource inconnue.", details)


def not_found(request: HttpRequest, exception: Exception | None = None) -> JsonResponse:
    """Handler Django (404) : une route inconnue répond au format unique."""
    return _json_404()


def bad_request(request: HttpRequest, exception: Exception | None = None) -> JsonResponse:
    """Handler Django (400) : requête refusée avant la vue."""
    return error_response(400, BAD_REQUEST, "Requête mal formée.")


def server_error(request: HttpRequest) -> JsonResponse:
    """Handler Django (500) : message générique, sans détail technique."""
    return error_response(500, INTERNAL_ERROR, INTERNAL_ERROR_MESSAGE)
