"""Validation des entrées de session et de compte.

Les erreurs sont **cumulées** puis renvoyées en 422 avec un détail par champ,
comme l'API publique : le client voit tout ce qui manque en un seul appel. Un
mot de passe n'est **jamais** réaffiché dans une erreur.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .. import config
from ..errors import field_error, validation_error

MAX_EMAIL_LENGTH = 254


def min_password_length() -> int:
    """Longueur minimale configurée (`INTERNAL_MIN_PASSWORD_LENGTH`)."""
    return int(
        getattr(settings, "INTERNAL_MIN_PASSWORD_LENGTH", config.MIN_PASSWORD_LENGTH)
    )


def credentials(
    payload: dict[str, Any],
    *,
    enforce_policy: bool = False,
) -> tuple[str, str]:
    """Extrait `(email, password)` d'un corps JSON, ou lève un 422 détaillé.

    Args:
        payload: corps JSON déjà décodé.
        enforce_policy: applique la longueur minimale (création de compte) ; la
            connexion se contente d'un mot de passe non vide, pour ne pas
            révéler la politique à un appelant non authentifié.
    """
    details: list[dict[str, str]] = []

    raw_email = payload.get("email")
    email = ""
    if not isinstance(raw_email, str) or not raw_email.strip():
        details.append(field_error("email", "Adresse e-mail requise."))
    else:
        email = raw_email.strip().lower()
        if len(email) > MAX_EMAIL_LENGTH:
            details.append(field_error("email", "Adresse e-mail trop longue."))
        else:
            try:
                validate_email(email)
            except ValidationError:
                details.append(field_error("email", "Adresse e-mail invalide."))

    raw_password = payload.get("password")
    password = ""
    if not isinstance(raw_password, str) or not raw_password:
        details.append(field_error("password", "Mot de passe requis."))
    else:
        password = raw_password
        minimum = min_password_length()
        if enforce_policy and len(password) < minimum:
            details.append(
                field_error(
                    "password",
                    f"Mot de passe trop court : {minimum} caractères minimum.",
                )
            )

    if details:
        raise validation_error(details)
    return email, password
