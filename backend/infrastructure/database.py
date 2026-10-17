"""Accès PostgreSQL de l'API publique.

Le moteur est construit **à la demande** :

- l'application démarre et sert sa route de santé sans base joignable ;
- une configuration absente produit une erreur explicite au moment où la donnée est
  réellement nécessaire, au lieu d'empêcher le démarrage.

Même convention que la plateforme data (`pipelines/db.py`, `ml/src/data.py`) : un
seul moteur par appel, construit depuis `DATABASE_URL`.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine

from . import config


def create_engine_from_env() -> Any:
    """Moteur SQLAlchemy sur la base applicative.

    Raises:
        MissingConfigurationError: si `DATABASE_URL` est absente (voir `config`).
    """
    return create_engine(config.database_url(), future=True)
