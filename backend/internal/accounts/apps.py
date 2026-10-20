"""Configuration de l'application `accounts`."""

from __future__ import annotations

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Comptes internes du back-office."""

    name = "backend.internal.accounts"
    label = "accounts"
