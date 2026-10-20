"""Consultation du journal d'audit (réservée au rôle `admin`).

Lecture seule : le journal n'a pas d'API de modification ni de suppression, une
entrée écrite reste consultable (durabilité de l'audit).
"""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse

from .. import config
from ..accounts.permissions import require_action
from ..accounts.roles import Action
from ..errors import api_view, require_methods
from ..params import integer
from .models import AuditEntry


@api_view
@require_methods("GET")
@require_action(Action.AUDIT_READ)
def entries(request: HttpRequest) -> JsonResponse:
    """Entrées les plus récentes d'abord, paginées, filtrables par action."""
    limit = integer(
        request,
        "limit",
        default=config.AUDIT_DEFAULT_LIMIT,
        minimum=1,
        maximum=config.AUDIT_MAX_LIMIT,
    )
    offset = integer(request, "offset", default=0, minimum=0)
    action = (request.GET.get("action") or "").strip()

    queryset = AuditEntry.objects.all()
    if action:
        queryset = queryset.filter(action=action)

    total = queryset.count()
    rows = queryset[offset : offset + limit]
    return JsonResponse(
        {
            "total": total,
            "limit": limit,
            "offset": offset,
            "entries": [row.as_dict() for row in rows],
        }
    )
