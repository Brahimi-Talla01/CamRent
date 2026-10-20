"""Cycle de vie des jetons d'accès internes.

Un jeton est une chaîne aléatoire de 32 octets (`secrets`). Il n'est renvoyé
qu'une fois — à la connexion — et seule son empreinte SHA-256 est stockée : le
hachage est rapide, ce qui est correct pour un jeton **aléatoire** de cette
entropie (contrairement à un mot de passe choisi par un humain, qui exige
PBKDF2). Un jeton expiré ou révoqué est refusé au même titre qu'un jeton inconnu.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from .. import config
from .models import AccessToken, InternalUser

TOKEN_BYTES = 32


@dataclass(frozen=True)
class IssuedToken:
    """Jeton émis : la valeur en clair (une seule fois) et son expiration."""

    token: str
    expires_at: datetime


def hash_token(raw: str) -> str:
    """Empreinte stockée en base."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def lifetime() -> timedelta:
    """Durée de vie configurée (`INTERNAL_TOKEN_TTL_HOURS`, défaut 12 h)."""
    hours = getattr(settings, "INTERNAL_TOKEN_TTL_HOURS", config.DEFAULT_TOKEN_TTL_HOURS)
    return timedelta(hours=int(hours))


def issue_token(user: InternalUser) -> IssuedToken:
    """Émet un nouveau jeton pour un compte actif."""
    raw = secrets.token_urlsafe(TOKEN_BYTES)
    expires_at = timezone.now() + lifetime()
    AccessToken.objects.create(user=user, key_hash=hash_token(raw), expires_at=expires_at)
    return IssuedToken(token=raw, expires_at=expires_at)


def resolve_token(raw: str) -> InternalUser | None:
    """Compte associé à un jeton utilisable, ou `None`."""
    access = (
        AccessToken.objects.select_related("user")
        .filter(
            key_hash=hash_token(raw),
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )
    if access is None:
        return None
    user = access.user
    return user if user.is_active else None


def revoke_token(raw: str) -> bool:
    """Révoque un jeton ; `True` si un jeton utilisable a bien été révoqué."""
    return bool(
        AccessToken.objects.filter(
            key_hash=hash_token(raw),
            revoked_at__isnull=True,
        ).update(revoked_at=timezone.now())
    )
