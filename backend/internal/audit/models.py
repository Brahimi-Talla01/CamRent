"""Entrée du journal d'audit : qui, quoi, sur quoi, quand, avec quel résultat.

Deux garanties de durabilité :

- `actor` est une clé étrangère `SET_NULL` **et** `actor_email` conserve
  l'adresse au moment de l'action : supprimer un compte ne doit pas effacer
  l'historique de ce qu'il a fait ;
- `details` ne porte que des métadonnées explicites (méthode, rôle, source) —
  jamais un mot de passe, un jeton ou un corps de requête (`audit.service`
  filtre ces clés, et les tests le vérifient).
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models


class Outcome(models.TextChoices):
    """Résultat d'une action journalisée."""

    SUCCESS = "success", "Succès"
    FAILED = "failed", "Échec"
    DENIED = "denied", "Refusé"


class AuditEntry(models.Model):
    """Une action sensible, journalisée et consultable."""

    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    #: Action au format `domaine.verbe` (ex. `users.create`, `auth.login`).
    action = models.CharField(max_length=64, db_index=True)
    outcome = models.CharField(max_length=16, choices=Outcome.choices)
    #: Compte auteur, si l'action a pu être attribuée à un compte.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    #: Instantané de l'adresse de l'auteur (survit à la suppression du compte).
    actor_email = models.CharField(max_length=254, blank=True)
    #: Cible de l'action (chemin, compte créé, ressource visée).
    target = models.CharField(max_length=254, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "internal_audit_entries"
        ordering = ["-occurred_at", "-id"]
        verbose_name = "entrée d'audit"
        verbose_name_plural = "entrées d'audit"

    def __str__(self) -> str:
        actor = self.actor_email or "anonyme"
        return f"{self.occurred_at.isoformat()} {actor} {self.action} ({self.outcome})"

    def as_dict(self) -> dict[str, Any]:
        """Forme exposée par `GET /internal/api/v1/audit`."""
        return {
            "id": self.pk,
            "occurred_at": self.occurred_at.isoformat(),
            "action": self.action,
            "outcome": self.outcome,
            "actor": self.actor_email or None,
            "target": self.target or None,
            "details": self.details or {},
        }
