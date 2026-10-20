"""Lecture des paramètres de requête, avec refus explicites (422).

Un paramètre mal formé ne doit jamais être ignoré en silence : il produit un
`validation_error` qui nomme le champ, comme les erreurs de corps.
"""

from __future__ import annotations

from django.http import HttpRequest

from .errors import field_error, validation_error


def integer(
    request: HttpRequest,
    name: str,
    *,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Entier de la chaîne de requête, borné, ou `default` s'il est absent."""
    raw = request.GET.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        raise validation_error([field_error(name, "Valeur entière attendue.")]) from None
    if minimum is not None and value < minimum:
        raise validation_error([field_error(name, f"Valeur minimale : {minimum}.")])
    if maximum is not None and value > maximum:
        raise validation_error([field_error(name, f"Valeur maximale : {maximum}.")])
    return value
