"""Configuration de l'application `audit`."""

from __future__ import annotations

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Journal des actions sensibles."""

    name = "backend.internal.audit"
    label = "audit"
