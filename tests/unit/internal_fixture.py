"""Constantes et helpers partagés des tests de l'API interne (08b.1).

Aucun de ces identifiants n'est un secret : ce sont des comptes de test créés
dans une base de test SQLite en mémoire.
"""

from __future__ import annotations

import json
from typing import Any

from django.test import Client

INTERNAL_PREFIX = "/internal/api/v1"
PUBLIC_PREFIX = "/api/v1"

ADMIN_EMAIL = "admin@camrent.test"
ADMIN_PASSWORD = "MotDePasseAdmin2026!"
SECOND_EMAIL = "second@camrent.test"
SECOND_PASSWORD = "MotDePasseSecond2026!"


def auth_headers(token: str) -> dict[str, str]:
    """En-tête d'authentification attendu par l'API interne."""
    return {"Authorization": f"Bearer {token}"}


def post_json(
    client: Client,
    path: str,
    payload: Any = None,
    *,
    token: str | None = None,
) -> Any:
    """POST JSON, avec ou sans jeton ; un corps `None` envoie un corps vide."""
    body = "" if payload is None else json.dumps(payload)
    headers = auth_headers(token) if token else None
    return client.post(path, data=body, content_type="application/json", headers=headers)


def get(
    client: Client,
    path: str,
    *,
    token: str | None = None,
    **params: object,
) -> Any:
    """GET avec paramètres de requête, avec ou sans jeton."""
    headers = auth_headers(token) if token else None
    return client.get(path, data=params, headers=headers)


def login(
    client: Client,
    email: str = ADMIN_EMAIL,
    password: str = ADMIN_PASSWORD,
) -> str:
    """Connexion réelle par l'API ; renvoie le jeton (échoue si la réponse n'est pas 200)."""
    response = post_json(
        client, f"{INTERNAL_PREFIX}/auth/login", {"email": email, "password": password}
    )
    assert response.status_code == 200, response.content
    token: str = response.json()["token"]
    return token
