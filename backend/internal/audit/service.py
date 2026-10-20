"""Écriture du journal d'audit — point d'entrée unique.

Toute action sensible passe par `record`, ce qui garantit la même forme
d'entrée (action, résultat, auteur, cible, détails) et le même filtre : les clés
qui pourraient porter un secret sont retirées avant écriture (`password`,
`token`, `secret`, `authorization`). Un appelant ne peut donc pas journaliser un
mot de passe par inadvertance.
"""

from __future__ import annotations

from typing import Any

from .models import AuditEntry, Outcome

#: Clés jamais écrites dans le journal, quelle que soit la source.
FORBIDDEN_DETAIL_KEYS = frozenset(
    {"password", "mot_de_passe", "token", "jeton", "secret", "authorization"}
)

MAX_TARGET_LENGTH = 254


def sanitize(details: dict[str, Any] | None) -> dict[str, Any]:
    """Retire les clés sensibles et ne garde que des valeurs simples."""
    if not details:
        return {}
    clean: dict[str, Any] = {}
    for key, value in details.items():
        if str(key).lower() in FORBIDDEN_DETAIL_KEYS:
            continue
        if isinstance(value, str | int | float | bool) or value is None:
            clean[str(key)] = value
        else:
            # Une structure imbriquée peut contenir n'importe quoi : on la refuse
            # plutôt que de prétendre l'avoir filtrée.
            clean[str(key)] = str(type(value).__name__)
    return clean


def record(
    *,
    action: str,
    outcome: Outcome,
    actor: Any = None,
    actor_email: str = "",
    target: str = "",
    details: dict[str, Any] | None = None,
) -> AuditEntry:
    """Écrit une entrée d'audit (qui, quoi, sur quoi, quand, résultat)."""
    email = actor_email or (getattr(actor, "email", "") or "")
    return AuditEntry.objects.create(
        action=action,
        outcome=outcome,
        actor=actor,
        actor_email=email[:MAX_TARGET_LENGTH],
        target=(target or "")[:MAX_TARGET_LENGTH],
        details=sanitize(details),
    )
