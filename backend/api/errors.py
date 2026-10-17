"""Gestion d'erreurs de l'API publique : un format unique, documenté.

Toutes les erreurs sortent sous la même forme (`backend.schemas.errors.ErrorBody`),
quel que soit le code HTTP. Aucune trace technique n'est renvoyée au client
(AGENTS.md §9) : une erreur est soit un refus de contrat (422, 400, 404), soit un
échec interne **générique** (500).

Codes stables exposés :

- `validation_error` (422) — l'entrée ne respecte pas le contrat ;
- `bad_request` (400) — requête mal formée mais comprise ;
- `method_not_allowed` (405) — méthode absente pour cette route ;
- `not_found` (404) — ressource ou valeur inconnue ;
- `internal_error` (500) — échec interne, sans détail technique.

Les gestionnaires sont branchés sur les classes **Starlette** : une route inconnue
(404) et une méthode non autorisée (405) sont levées par Starlette lui-même, en
amont de FastAPI — les brancher sur la seule classe FastAPI laisserait ces deux cas
hors du format unique.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

VALIDATION_ERROR_CODE = "validation_error"
BAD_REQUEST_CODE = "bad_request"
METHOD_NOT_ALLOWED_CODE = "method_not_allowed"
NOT_FOUND_CODE = "not_found"
INTERNAL_ERROR_CODE = "internal_error"

STATUS_CODES: dict[int, str] = {
    400: BAD_REQUEST_CODE,
    404: NOT_FOUND_CODE,
    405: METHOD_NOT_ALLOWED_CODE,
    422: VALIDATION_ERROR_CODE,
}

INTERNAL_ERROR_MESSAGE = "Erreur interne du service."


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> JSONResponse:
    """Construit une réponse d'erreur au format unique de l'API."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            }
        },
    )


def _field_path(location: tuple[object, ...]) -> str:
    """Chemin lisible d'un champ, sans le préfixe `body` ajouté par FastAPI."""
    return ".".join(str(part) for part in location if part != "body")


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Refus de contrat (422) : un détail par champ concerné."""
    details = [
        {"field": _field_path(tuple(error.get("loc", ()))), "message": error.get("msg", "")}
        for error in exc.errors()
    ]
    return error_response(
        422, VALIDATION_ERROR_CODE, "Entrée invalide.", details
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Erreur HTTP prévue (400, 404, 405, …) au format unique."""
    code = STATUS_CODES.get(exc.status_code, "error")
    return error_response(exc.status_code, code, str(exc.detail))


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Échec interne : réponse générique, journal sans donnée sensible.

    Seuls la classe de l'exception et le chemin sont journalisés : un message
    d'exception peut contenir une valeur d'entrée ou un identifiant de connexion.
    """
    logger.error("Échec interne non géré (%s) sur %s", type(exc).__name__, request.url.path)
    return error_response(500, INTERNAL_ERROR_CODE, INTERNAL_ERROR_MESSAGE)


def register_error_handlers(app: FastAPI) -> None:
    """Branche les gestionnaires d'erreurs sur l'application."""
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
