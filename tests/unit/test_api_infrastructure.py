"""Tests de la configuration du backend.

Deux invariants : l'absence de configuration produit une erreur **explicite**, et
cette erreur ne contient jamais d'identifiants.
"""

from __future__ import annotations

import pytest

from backend.infrastructure import config, database


def test_database_url_is_read_from_environment(monkeypatch) -> None:
    monkeypatch.setenv(config.DATABASE_URL_ENV, "postgresql://u:p@localhost:5432/db")

    assert config.database_url() == "postgresql://u:p@localhost:5432/db"


@pytest.mark.parametrize("value", ["", "   "])
def test_missing_database_url_raises_explicit_error(monkeypatch, value: str) -> None:
    monkeypatch.setenv(config.DATABASE_URL_ENV, value)

    with pytest.raises(config.MissingConfigurationError) as exc_info:
        config.database_url()

    message = str(exc_info.value)
    assert config.DATABASE_URL_ENV in message  # la variable à définir est nommée
    assert "change-me" not in message  # aucune valeur d'identifiant reprise


def test_engine_creation_reports_missing_configuration(monkeypatch) -> None:
    """Le moteur échoue au moment de l'usage, avec la même erreur explicite."""
    monkeypatch.delenv(config.DATABASE_URL_ENV, raising=False)

    with pytest.raises(config.MissingConfigurationError):
        database.create_engine_from_env()


def test_api_is_versioned_under_a_prefix() -> None:
    assert config.API_PREFIX == "/api/v1"
