"""Rôles internes et actions protégées — **autorisation minimale par action**.

Décision de périmètre (ticket #61, spec 13 §Scope Limits) : un seul rôle est
ouvert, `admin`. Aucun rôle intermédiaire n'est ajouté tant qu'un besoin mesuré
ne le justifie pas. La granularité préparée est néanmoins **par action** : chaque
route déclare l'action qu'elle protège, et une action n'est ouverte qu'aux rôles
listés dans `ACTION_ROLES`. Ajouter un rôle demain se fait donc par cette table,
route par route, sans toucher aux vues.

Le contrôle échoue **fermé** : une action absente de la table, ou un rôle
inconnu (donnée ancienne, import manuel), n'ouvre aucun accès.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from django.db import models


class Role(models.TextChoices):
    """Rôles internes ouverts. Un seul pour l'instant (décision 08b.1)."""

    ADMIN = "admin", "Administrateur"


class Action(StrEnum):
    """Actions sensibles de l'API interne, nommées comme dans l'audit."""

    # Session
    SESSION_LOGIN = "auth.login"
    SESSION_LOGOUT = "auth.logout"
    SESSION_READ = "auth.read"
    # Comptes internes
    USERS_CREATE = "users.create"
    # Audit
    AUDIT_READ = "audit.read"


#: Action → rôles autorisés. Seul `admin` existe ; la table reste explicite pour
#: que chaque route déclare son autorisation, et pour qu'un futur rôle s'ajoute
#: ici plutôt que par une condition dispersée dans les vues.
ACTION_ROLES: Final[dict[str, frozenset[str]]] = {
    Action.SESSION_LOGOUT.value: frozenset({Role.ADMIN}),
    Action.SESSION_READ.value: frozenset({Role.ADMIN}),
    Action.USERS_CREATE.value: frozenset({Role.ADMIN}),
    Action.AUDIT_READ.value: frozenset({Role.ADMIN}),
}


def roles_for(action: Action) -> frozenset[str]:
    """Rôles autorisés pour une action (ensemble vide si l'action est inconnue)."""
    return ACTION_ROLES.get(action.value, frozenset())
