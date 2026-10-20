"""Crée le premier compte interne (bootstrap du back-office).

Sans ce chemin, aucun compte n'existerait et `POST /internal/api/v1/users`,
réservé à un `admin` authentifié, serait inaccessible. La commande est donc le
seul point d'amorçage ; elle journalise elle-même son action (`actor=None`,
source `cli`), pour que la création du premier compte soit traçable.
"""

from __future__ import annotations

import getpass

from django.core.management.base import BaseCommand, CommandError

from ....audit.models import Outcome
from ....audit.service import record
from ...models import InternalUser
from ...roles import Action, Role
from ...validation import min_password_length


class Command(BaseCommand):
    """Crée un compte interne `admin` sans passer par l'API."""

    help = "Crée un compte interne admin (bootstrap de l'API interne)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--email", required=True, help="Adresse e-mail du compte.")
        parser.add_argument(
            "--password",
            default=None,
            help="Mot de passe (saisie masquée et recommandée si l'option est omise).",
        )

    def handle(self, *args, **options) -> None:
        email = str(options["email"]).strip().lower()
        if not email:
            raise CommandError("L'adresse e-mail est obligatoire.")

        password = options["password"] or getpass.getpass("Mot de passe (invisible) : ")
        minimum = min_password_length()
        if len(password) < minimum:
            raise CommandError(f"Mot de passe trop court : {minimum} caractères minimum.")

        if InternalUser.objects.filter(email__iexact=email).exists():
            raise CommandError(f"Un compte interne existe déjà : {email}")

        user = InternalUser.objects.create_user(
            email=email, password=password, role=Role.ADMIN
        )
        record(
            action=Action.USERS_CREATE.value,
            outcome=Outcome.SUCCESS,
            actor_email=user.email,
            target=f"internal-user:{user.email}",
            details={"role": user.role, "source": "cli"},
        )
        # Aucun mot de passe, aucun hachage : seulement l'identité créée.
        self.stdout.write(
            self.style.SUCCESS(f"Compte interne créé : {user.email} (rôle {user.role})")
        )
