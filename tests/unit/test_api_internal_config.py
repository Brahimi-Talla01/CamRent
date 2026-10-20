"""Configuration de l'API interne : aucun secret en dur, erreurs explicites.

Les réglages réels sont **réexécutés** dans un environnement vidé (via
`runpy`), pour vérifier qu'aucune valeur n'est inventée quand une variable
d'environnement manque, et que le message d'erreur nomme la variable sans
reprendre d'identifiant (AGENTS.md §9).
"""

from __future__ import annotations

import os
import runpy
from typing import Any
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

DATABASE_URL = "postgresql://camrent:change-me@localhost:5433/camrent"


def load_settings(environment: dict[str, str]) -> dict[str, Any]:
    """Exécute `backend/internal/settings.py` dans un environnement contrôlé."""
    with mock.patch.dict(os.environ, environment, clear=True):
        return runpy.run_module("backend.internal.settings", run_name="probe_settings")


def test_settings_require_the_secret_key() -> None:
    with pytest.raises(ImproperlyConfigured, match="INTERNAL_SECRET_KEY"):
        load_settings({"DATABASE_URL": DATABASE_URL})


def test_settings_require_the_database_url() -> None:
    with pytest.raises(ImproperlyConfigured, match="DATABASE_URL"):
        load_settings({"INTERNAL_SECRET_KEY": "x" * 60})


def test_settings_never_expose_credentials_in_errors() -> None:
    with pytest.raises(ImproperlyConfigured) as excinfo:
        load_settings({})

    assert "change-me" not in str(excinfo.value)


def test_settings_read_every_value_from_the_environment() -> None:
    settings = load_settings(
        {
            "INTERNAL_SECRET_KEY": "cle-de-test-suffisamment-longue-pour-django-000",
            "DATABASE_URL": DATABASE_URL,
            "INTERNAL_DEBUG": "true",
            "INTERNAL_ALLOWED_HOSTS": "api.interne.local, 127.0.0.1",
            "INTERNAL_TOKEN_TTL_HOURS": "2",
        }
    )

    assert settings["DEBUG"] is True
    assert settings["ALLOWED_HOSTS"] == ["api.interne.local", "127.0.0.1"]
    assert settings["INTERNAL_TOKEN_TTL_HOURS"] == 2
    assert settings["DATABASES"]["default"]["NAME"] == "camrent"
    assert settings["DATABASES"]["default"]["HOST"] == "localhost"
    assert settings["DATABASES"]["default"]["PORT"] == "5433"


def test_settings_default_to_no_debug_and_short_lived_tokens() -> None:
    settings = load_settings(
        {
            "INTERNAL_SECRET_KEY": "cle-de-test-suffisamment-longue-pour-django-000",
            "DATABASE_URL": DATABASE_URL,
        }
    )

    assert settings["DEBUG"] is False
    assert settings["ALLOWED_HOSTS"] == ["localhost", "127.0.0.1"]
    assert settings["INTERNAL_TOKEN_TTL_HOURS"] == 12


@pytest.mark.parametrize("value", ["0", "-3", "douze"])
def test_invalid_token_lifetime_is_refused(value: str) -> None:
    with pytest.raises(ImproperlyConfigured, match="INTERNAL_TOKEN_TTL_HOURS"):
        load_settings(
            {
                "INTERNAL_SECRET_KEY": "cle-de-test-suffisamment-longue-pour-django-000",
                "DATABASE_URL": DATABASE_URL,
                "INTERNAL_TOKEN_TTL_HOURS": value,
            }
        )


def test_database_url_is_parsed_for_django() -> None:
    from backend.internal.database import from_url

    parsed = from_url("postgresql://utilisateur:mot%40depasse@db.interne:6543/camrent")

    assert parsed["ENGINE"] == "django.db.backends.postgresql"
    assert parsed["NAME"] == "camrent"
    assert parsed["USER"] == "utilisateur"
    assert parsed["PASSWORD"] == "mot@depasse"
    assert parsed["HOST"] == "db.interne"
    assert parsed["PORT"] == "6543"


@pytest.mark.parametrize(
    "url",
    [
        "",
        "sqlite:///camrent.db",
        "mysql://camrent:change-me@localhost/camrent",
        "postgresql://camrent:change-me@localhost:5433",
    ],
)
def test_non_postgres_or_incomplete_database_urls_are_refused(url: str) -> None:
    from backend.internal.database import from_url

    with pytest.raises(ImproperlyConfigured):
        from_url(url)


def test_test_settings_do_not_need_any_secret() -> None:
    """La suite unitaire tourne sans environnement : c'est la garantie des réglages de test."""
    from django.conf import settings

    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert settings.SECRET_KEY.startswith("test-only")


def test_internal_api_lives_outside_the_public_app_configuration() -> None:
    """Les deux applications ne partagent ni préfixe ni modèle de compte."""
    from django.conf import settings as django_settings

    from backend.infrastructure import config as public_config

    assert public_config.API_PREFIX == "/api/v1"
    assert django_settings.INTERNAL_API_VERSION == "0.1.0"
    assert "backend.internal.accounts" in django_settings.INSTALLED_APPS
    assert "backend.api" not in django_settings.INSTALLED_APPS
