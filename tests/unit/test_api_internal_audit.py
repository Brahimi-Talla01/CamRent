"""Journal d'audit : qui, quoi, sur quoi, quand (ticket #61).

Chaque action sensible testée passe par l'API réelle ; le journal est ensuite
relu par la route consultable, comme le ferait le back-office.
"""

from __future__ import annotations

import json

import pytest

from tests.unit.internal_fixture import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    INTERNAL_PREFIX,
    SECOND_EMAIL,
    SECOND_PASSWORD,
    login,
    post_json,
)

pytestmark = pytest.mark.django_db

AUDIT_URL = f"{INTERNAL_PREFIX}/audit"
LOGIN_URL = f"{INTERNAL_PREFIX}/auth/login"
LOGOUT_URL = f"{INTERNAL_PREFIX}/auth/logout"
USERS_URL = f"{INTERNAL_PREFIX}/users"


def _entries(client, headers, **params) -> list[dict]:
    response = client.get(AUDIT_URL, data=params, headers=headers)
    assert response.status_code == 200, response.content
    return response.json()["entries"]


def test_successful_login_is_audited(client, internal_admin, admin_headers) -> None:
    post_json(client, LOGIN_URL, {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    entries = _entries(client, admin_headers)

    assert len(entries) == 1
    entry = entries[0]
    assert entry["action"] == "auth.login"
    assert entry["outcome"] == "success"
    assert entry["actor"] == ADMIN_EMAIL
    assert entry["target"] == "internal-api/session"
    assert entry["occurred_at"]
    assert entry["details"] == {}


def test_failed_login_is_audited_without_actor(client, internal_admin, admin_headers) -> None:
    post_json(client, LOGIN_URL, {"email": "inconnu@camrent.test", "password": "mauvais"})

    entry = _entries(client, admin_headers)[0]

    assert entry["action"] == "auth.login"
    assert entry["outcome"] == "failed"
    assert entry["actor"] == "inconnu@camrent.test"
    assert entry["details"] == {}


def test_logout_is_audited(client, internal_admin, admin_headers) -> None:
    token = login(client)

    post_json(client, LOGOUT_URL, {}, token=token)
    entries = _entries(client, admin_headers)

    actions = {(entry["action"], entry["outcome"]) for entry in entries}
    assert ("auth.login", "success") in actions
    assert ("auth.logout", "success") in actions


def test_account_creation_is_audited(client, internal_admin, admin_headers) -> None:
    client.post(
        USERS_URL,
        data={"email": SECOND_EMAIL, "password": SECOND_PASSWORD},
        content_type="application/json",
        headers=admin_headers,
    )

    entry = _entries(client, admin_headers, action="users.create")[0]

    assert entry["action"] == "users.create"
    assert entry["outcome"] == "success"
    assert entry["actor"] == ADMIN_EMAIL
    assert entry["target"] == f"internal-user:{SECOND_EMAIL}"
    assert entry["details"] == {"role": "admin"}


def test_audit_never_contains_a_password_or_a_token(
    client, internal_admin, admin_headers
) -> None:
    token = login(client)

    body = client.get(AUDIT_URL, headers=admin_headers).content.decode()

    assert ADMIN_PASSWORD not in body
    assert token not in body
    assert "password" not in json.dumps(
        [entry["details"] for entry in _entries(client, admin_headers)]
    )


def test_sensitive_keys_are_filtered_before_writing() -> None:
    from backend.internal.audit.models import Outcome
    from backend.internal.audit.service import record

    entry = record(
        action="users.create",
        outcome=Outcome.SUCCESS,
        actor_email=ADMIN_EMAIL,
        details={
            "password": "secret-en-clair",
            "token": "jeton",
            "Authorization": "Bearer x",
            "role": "admin",
        },
    )

    assert entry.details == {"role": "admin"}


def test_audit_is_paginated_newest_first(client, internal_admin, admin_headers) -> None:
    from backend.internal.audit.models import Outcome
    from backend.internal.audit.service import record

    for action in ("auth.read", "users.create", "audit.read"):
        record(action=action, outcome=Outcome.SUCCESS, actor=internal_admin)

    response = client.get(AUDIT_URL, data={"limit": 2, "offset": 0}, headers=admin_headers)
    body = response.json()

    assert body["total"] == 3
    assert body["limit"] == 2
    assert [entry["action"] for entry in body["entries"]] == ["audit.read", "users.create"]

    second = client.get(
        AUDIT_URL, data={"limit": 2, "offset": 2}, headers=admin_headers
    ).json()
    assert [entry["action"] for entry in second["entries"]] == ["auth.read"]


def test_audit_can_be_filtered_by_action(client, internal_admin, admin_headers) -> None:
    from backend.internal.audit.models import Outcome
    from backend.internal.audit.service import record

    record(action="auth.read", outcome=Outcome.SUCCESS, actor=internal_admin)
    record(action="users.create", outcome=Outcome.SUCCESS, actor=internal_admin)

    entries = _entries(client, admin_headers, action="users.create")

    assert len(entries) == 1
    assert entries[0]["action"] == "users.create"


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 500},
        {"limit": "trois"},
        {"offset": -1},
    ],
)
def test_invalid_pagination_is_refused(client, internal_admin, admin_headers, params) -> None:
    response = client.get(AUDIT_URL, data=params, headers=admin_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_audit_is_read_only(client, internal_admin, admin_headers) -> None:
    response = client.post(
        AUDIT_URL, data="{}", content_type="application/json", headers=admin_headers
    )

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_default_pagination_limits_the_page(client, internal_admin, admin_headers) -> None:
    from backend.internal.audit.models import Outcome
    from backend.internal.audit.service import record

    record(action="auth.read", outcome=Outcome.SUCCESS, actor=internal_admin)

    body = client.get(AUDIT_URL, headers=admin_headers).json()

    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["total"] == 1
