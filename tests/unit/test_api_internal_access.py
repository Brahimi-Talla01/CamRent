"""Accès de l'API interne et frontière public / interne (ticket #61).

Deux refus sont exigés par le ticket et testés ici : **non authentifié** (401)
et **rôle insuffisant** (403). Le second est vérifié avec un compte dont le rôle
n'ouvre aucune action : le contrôle échoue fermé, même si un rôle inconnu
apparaissait en base (import manuel, donnée ancienne) — aucun second rôle n'est
ouvert dans le produit (décision 08b.1).
"""

from __future__ import annotations

import pytest

from tests.unit.internal_fixture import (
    ADMIN_EMAIL,
    INTERNAL_PREFIX,
    PUBLIC_PREFIX,
    SECOND_EMAIL,
    SECOND_PASSWORD,
    get,
    login,
    post_json,
)

pytestmark = pytest.mark.django_db

ME_URL = f"{INTERNAL_PREFIX}/me"
AUDIT_URL = f"{INTERNAL_PREFIX}/audit"
USERS_URL = f"{INTERNAL_PREFIX}/users"
LOGOUT_URL = f"{INTERNAL_PREFIX}/auth/logout"
LOGIN_URL = f"{INTERNAL_PREFIX}/auth/login"


@pytest.fixture
def reader(db):
    """Compte interne au rôle non déclaré : n'ouvre aucune action."""
    from backend.internal.accounts.models import InternalUser

    return InternalUser.objects.create_user(
        email="lecteur@camrent.test",
        password="MotDePasseLecteur2026!",
        role="reader",
    )


@pytest.fixture
def reader_token(reader) -> str:
    from backend.internal.accounts.tokens import issue_token

    return issue_token(reader).token


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", ME_URL, None),
        ("get", AUDIT_URL, None),
        (
            "post",
            USERS_URL,
            {"email": "nouveau@camrent.test", "password": "MotDePasseNouveau2026!"},
        ),
        ("post", LOGOUT_URL, {}),
    ],
)
def test_unauthenticated_request_is_refused(client, method, path, payload) -> None:
    if method == "get":
        response = get(client, path)
    else:
        response = post_json(client, path, payload)

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "unauthenticated"
    assert error["details"][0]["field"] == "Authorization"


def test_unauthenticated_refusals_are_not_written_to_the_audit(client, internal_admin) -> None:
    """Un appelant anonyme ne peut pas remplir le journal d'audit."""
    from backend.internal.audit.models import AuditEntry

    get(client, ME_URL)
    get(client, AUDIT_URL)
    post_json(client, LOGOUT_URL, {})

    assert AuditEntry.objects.count() == 0


def test_insufficient_role_is_refused_and_audited(client, reader_token) -> None:
    response = get(client, ME_URL, token=reader_token)

    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "forbidden"
    assert error["message"] == "Accès refusé pour ce rôle."

    from backend.internal.audit.models import AuditEntry

    entry = AuditEntry.objects.get(action="auth.read")
    assert entry.outcome == "denied"
    assert entry.actor_email == "lecteur@camrent.test"
    assert entry.target == ME_URL


def test_insufficient_role_cannot_create_accounts(client, reader_token) -> None:
    response = post_json(
        client,
        USERS_URL,
        {"email": "intrus@camrent.test", "password": "MotDePasseIntrus2026!"},
        token=reader_token,
    )

    assert response.status_code == 403

    from backend.internal.accounts.models import InternalUser

    assert not InternalUser.objects.filter(email="intrus@camrent.test").exists()


def test_admin_can_create_another_internal_account(client, admin_headers) -> None:
    response = client.post(
        USERS_URL,
        data={"email": SECOND_EMAIL, "password": SECOND_PASSWORD},
        content_type="application/json",
        headers=admin_headers,
    )

    assert response.status_code == 201
    assert response.json()["user"] == {"email": SECOND_EMAIL, "role": "admin"}
    # Le nouveau compte se connecte réellement.
    assert login(client, SECOND_EMAIL, SECOND_PASSWORD)


def test_created_account_stores_a_hash_never_the_password(client, admin_headers) -> None:
    client.post(
        USERS_URL,
        data={"email": SECOND_EMAIL, "password": SECOND_PASSWORD},
        content_type="application/json",
        headers=admin_headers,
    )

    from backend.internal.accounts.models import InternalUser

    user = InternalUser.objects.get(email=SECOND_EMAIL)
    assert user.password != SECOND_PASSWORD
    assert user.check_password(SECOND_PASSWORD)


def test_account_creation_enforces_password_policy(client, admin_headers) -> None:
    response = client.post(
        USERS_URL,
        data={"email": SECOND_EMAIL, "password": "court"},
        content_type="application/json",
        headers=admin_headers,
    )

    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert details[0]["field"] == "password"
    assert "12" in details[0]["message"]


def test_account_creation_rejects_duplicate_email(client, admin_headers) -> None:
    response = client.post(
        USERS_URL,
        data={"email": ADMIN_EMAIL, "password": SECOND_PASSWORD},
        content_type="application/json",
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_method_not_allowed_is_a_json_error(client, admin_headers) -> None:
    response = client.post(ME_URL, headers=admin_headers)

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_unknown_internal_route_is_a_json_404(client, admin_headers) -> None:
    response = client.get(f"{INTERNAL_PREFIX}/inconnu", headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize(
    "public_path",
    [
        f"{PUBLIC_PREFIX}/health",
        f"{PUBLIC_PREFIX}/predictions",
        f"{PUBLIC_PREFIX}/market/cities",
        "/health",
    ],
)
def test_internal_app_does_not_expose_public_routes(client, admin_headers, public_path) -> None:
    response = client.get(public_path, headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_public_app_does_not_expose_internal_routes() -> None:
    from fastapi.testclient import TestClient

    from backend.api.app import create_app

    public = TestClient(create_app())

    assert public.get("/api/v1/health").status_code == 200
    for path in ("/internal/api/v1/health", "/internal/api/v1/audit", "/internal/api/v1/me"):
        response = public.get(path)
        assert response.status_code == 404, path
        assert response.json()["error"]["code"] == "not_found", path


def test_unknown_role_fails_closed_at_model_level() -> None:
    from backend.internal.accounts.models import InternalUser
    from backend.internal.accounts.roles import Action, Role, roles_for

    assert roles_for(Action.SESSION_READ) == frozenset({Role.ADMIN})
    # Une action non déclarée n'ouvre aucun accès (fermé par défaut).
    assert roles_for(Action.SESSION_LOGIN) == frozenset()
    assert not InternalUser(role=Role.ADMIN).can_perform(Action.SESSION_LOGIN)
    assert InternalUser(role=Role.ADMIN).can_perform(Action.SESSION_READ)
