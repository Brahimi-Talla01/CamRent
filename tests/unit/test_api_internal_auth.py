"""Session de l'API interne : connexion, jeton, déconnexion (ticket #61).

Aucun jeton n'est simulé : chaque test passe par les vues réelles, sur une base
de test SQLite en mémoire (voir `backend/internal/settings_test.py`).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from tests.unit.internal_fixture import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    INTERNAL_PREFIX,
    auth_headers,
    get,
    login,
    post_json,
)

pytestmark = pytest.mark.django_db

LOGIN_URL = f"{INTERNAL_PREFIX}/auth/login"
LOGOUT_URL = f"{INTERNAL_PREFIX}/auth/logout"
ME_URL = f"{INTERNAL_PREFIX}/me"
HEALTH_URL = f"{INTERNAL_PREFIX}/health"


def test_health_is_public_and_versioned(client) -> None:
    response = get(client, HEALTH_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_prefix"] == INTERNAL_PREFIX
    assert body["api_version"] == "0.1.0"
    assert body["auth"] == "required"


def test_health_refuses_other_methods(client) -> None:
    response = post_json(client, HEALTH_URL, {})

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_login_issues_token_and_role(client, internal_admin) -> None:
    response = post_json(client, LOGIN_URL, {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store"
    body = response.json()
    assert isinstance(body["token"], str) and len(body["token"]) >= 32
    assert body["user"] == {"email": ADMIN_EMAIL, "role": "admin"}
    assert datetime.fromisoformat(body["expires_at"]) > timezone.now()


def test_login_never_exposes_password_or_hash(client, internal_admin) -> None:
    response = post_json(client, LOGIN_URL, {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    body = response.json()
    assert "password" not in body
    assert ADMIN_PASSWORD not in response.content.decode()
    assert internal_admin.password != ADMIN_PASSWORD
    assert internal_admin.check_password(ADMIN_PASSWORD)


def test_login_email_is_case_and_space_insensitive(client, internal_admin) -> None:
    response = post_json(
        client, LOGIN_URL, {"email": f"  {ADMIN_EMAIL.upper()} ", "password": ADMIN_PASSWORD}
    )

    assert response.status_code == 200


def test_wrong_password_is_refused_without_detail(client, internal_admin) -> None:
    response = post_json(client, LOGIN_URL, {"email": ADMIN_EMAIL, "password": "mauvais-secret"})

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "invalid_credentials"
    assert error["message"] == "Identifiants invalides."
    assert error["details"] == []
    assert "mauvais-secret" not in response.content.decode()


def test_unknown_account_is_indistinguishable_from_wrong_password(client, internal_admin) -> None:
    unknown = post_json(
        client, LOGIN_URL, {"email": "inconnu@camrent.test", "password": ADMIN_PASSWORD}
    )
    wrong = post_json(client, LOGIN_URL, {"email": ADMIN_EMAIL, "password": "faux-mot-de-passe"})

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_inactive_account_cannot_log_in(client, internal_admin) -> None:
    internal_admin.is_active = False
    internal_admin.save(update_fields=["is_active"])

    response = post_json(client, LOGIN_URL, {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_login_missing_fields_lists_every_field(client, internal_admin) -> None:
    response = post_json(client, LOGIN_URL, {})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert {detail["field"] for detail in error["details"]} == {"email", "password"}


def test_login_without_body_is_a_contract_error(client) -> None:
    response = post_json(client, LOGIN_URL, None)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "body"


def test_login_malformed_json_is_a_bad_request(client) -> None:
    response = client.post(LOGIN_URL, data="{pas du json", content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"


def test_me_returns_the_authenticated_account(client, internal_admin) -> None:
    token = login(client)

    response = get(client, ME_URL, token=token)

    assert response.status_code == 200
    assert response.json() == {"user": {"email": ADMIN_EMAIL, "role": "admin"}}


def test_me_requires_a_token(client, internal_admin) -> None:
    response = get(client, ME_URL)

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "unauthenticated"
    assert error["details"][0]["field"] == "Authorization"


@pytest.mark.parametrize(
    "header",
    [
        {"Authorization": "Bearer "},
        {"Authorization": "Bearer inconnu"},
        {"Authorization": "Basic YWRtaW46YWRtaW4="},
        {"Authorization": "Bearer"},
        {},
    ],
)
def test_me_refuses_unusable_authorization_headers(client, internal_admin, header) -> None:
    response = client.get(ME_URL, headers=header)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_expired_token_is_refused(client, internal_admin) -> None:
    from backend.internal.accounts.models import AccessToken

    token = login(client)
    AccessToken.objects.filter(user=internal_admin).update(
        expires_at=timezone.now() - timedelta(minutes=1)
    )

    response = get(client, ME_URL, token=token)

    assert response.status_code == 401


def test_token_of_deactivated_account_is_refused(client, internal_admin) -> None:
    token = login(client)
    internal_admin.is_active = False
    internal_admin.save(update_fields=["is_active"])

    response = get(client, ME_URL, token=token)

    assert response.status_code == 401


def test_logout_revokes_the_token(client, internal_admin) -> None:
    token = login(client)

    response = post_json(client, LOGOUT_URL, {}, token=token)

    assert response.status_code == 204
    assert get(client, ME_URL, token=token).status_code == 401
    # Un jeton révoqué ne peut pas resservir pour se déconnecter.
    assert post_json(client, LOGOUT_URL, {}, token=token).status_code == 401


def test_login_is_not_allowed_with_get(client) -> None:
    response = client.get(LOGIN_URL)

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_token_header_is_not_logged_by_the_api(client, internal_admin) -> None:
    """Le jeton ne doit apparaître ni dans la réponse, ni dans une entrée d'audit."""
    token = login(client)
    body = get(client, f"{INTERNAL_PREFIX}/audit", token=token).content.decode()

    assert token not in body
    assert auth_headers(token)["Authorization"] not in body
