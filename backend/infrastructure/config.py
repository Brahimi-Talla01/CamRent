"""Configuration de l'API publique.

Aucun secret ni chemin en dur (AGENTS.md §3 et §9, code-standards §Python) : tout
passe par des variables d'environnement, lues **à l'appel** et non à l'import, pour
que les tests puissent les poser ou les retirer sans redémarrer le processus.
"""

from __future__ import annotations

import os
from typing import Final

API_TITLE: Final[str] = "CamRent — API publique"
# Version du **contrat** d'API (`/api/v1`). À ne pas confondre avec la version du
# modèle servi : celle-ci est épinglée dans `ml/models/champion.json` (Phase 7) et
# exposée dans les réponses de prédiction.
API_VERSION: Final[str] = "0.1.0"
API_PREFIX: Final[str] = "/api/v1"

# Variable d'environnement de la base applicative (marts de marché). Le nom est
# celui déjà utilisé par `pipelines` et `ml` : une seule variable pour une seule base.
DATABASE_URL_ENV: Final[str] = "DATABASE_URL"

# Schéma des marts de marché. Même variable que `ml/src/config.py`, pour que l'API
# et l'entraînement lisent le même emplacement. La CI construit les marts dans un
# schéma dédié (`analytics_ci_marts`) et la surcharge dans ses étapes de données.
MARTS_SCHEMA_ENV: Final[str] = "DBT_MARTS_SCHEMA"
DEFAULT_MARTS_SCHEMA: Final[str] = "analytics_marts"


class MissingConfigurationError(RuntimeError):
    """Configuration requise absente de l'environnement."""


def database_url() -> str:
    """URL PostgreSQL de la base applicative.

    Raises:
        MissingConfigurationError: si `DATABASE_URL` est absente. Le message nomme la
            variable manquante sans jamais afficher d'identifiants (AGENTS.md §9).
    """
    value = os.environ.get(DATABASE_URL_ENV, "").strip()
    if not value:
        raise MissingConfigurationError(
            f"{DATABASE_URL_ENV} est requise pour interroger les marts de marché. "
            "Format attendu : postgresql://<utilisateur>:<mot de passe>@<hôte>:<port>/<base> "
            "(voir `.env.example`)."
        )
    return value


def market_marts_schema() -> str:
    """Schéma PostgreSQL des marts de marché (défaut : ``analytics_marts``)."""
    value = os.environ.get(MARTS_SCHEMA_ENV, "").strip()
    return value or DEFAULT_MARTS_SCHEMA
