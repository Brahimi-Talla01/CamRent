"""Route de santé de l'API interne : le service répond-il, et sous quel contrat ?

C'est la **seule** route sans authentification : elle ne lit ni base ni modèle
et ne révèle rien d'exploitable. Elle sert à distinguer « service arrêté » de
« jeton refusé » avant de disposer d'un compte.
"""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse

from . import config
from .errors import api_view, require_methods


@api_view
@require_methods("GET")
def health(request: HttpRequest) -> JsonResponse:
    """État du service et version du contrat interne."""
    return JsonResponse(
        {
            "status": "ok",
            "api_version": config.API_VERSION,
            "api_prefix": config.API_PREFIX,
            "auth": "required",
        }
    )
