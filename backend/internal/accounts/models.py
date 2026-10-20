"""Comptes internes et jetons d'accès de l'API interne.

Deux choix structurants :

- **Modèle de compte dédié** (`AbstractBaseUser`, pas `django.contrib.auth`) :
  l'autorisation du back-office est un rôle + une action, pas les permissions
  Django. Aucun `django.contrib.admin` n'est monté — l'interface viendra en
  phase 9b et consommera cette API.
- **Jeton opaque haché en base** : le jeton n'est affiché qu'une fois, à la
  connexion ; seule son empreinte SHA-256 est stockée. Un vol de base ne donne
  donc pas de session utilisable, et le jeton n'apparaît jamais dans un journal.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from .roles import Action, Role, roles_for


class InternalUserManager(BaseUserManager):
    """Création des comptes internes (mot de passe toujours haché)."""

    use_in_migrations = True

    def create_user(
        self,
        email: str,
        password: str | None = None,
        role: str = Role.ADMIN,
        **extra: Any,
    ) -> InternalUser:
        """Crée un compte interne ; sans mot de passe, le compte est inutilisable."""
        if not email or not email.strip():
            raise ValueError("Un compte interne exige une adresse e-mail.")
        user = self.model(email=email.strip().lower(), role=role, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user


class InternalUser(AbstractBaseUser):
    """Compte du back-office : une adresse, un rôle, un état actif."""

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=32, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = InternalUserManager()

    class Meta:
        db_table = "internal_users"
        ordering = ["email"]
        verbose_name = "compte interne"
        verbose_name_plural = "comptes internes"

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    def can_perform(self, action: Action) -> bool:
        """Le rôle du compte ouvre-t-il cette action ? (échoue fermé)"""
        return self.role in roles_for(action)


class AccessToken(models.Model):
    """Jeton d'accès opaque, stocké haché, avec expiration et révocation."""

    user = models.ForeignKey(
        InternalUser,
        on_delete=models.CASCADE,
        related_name="access_tokens",
    )
    #: Empreinte SHA-256 du jeton. Le jeton en clair n'est jamais stocké.
    key_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "internal_access_tokens"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["key_hash", "revoked_at"])]

    def __str__(self) -> str:
        return f"jeton de {self.user_id} (expire {self.expires_at.isoformat()})"
