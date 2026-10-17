"""Forme unique des erreurs de l'API publique.

Un seul format, quel que soit le code HTTP, pour que le client n'ait pas à
interpréter deux structures selon le cas :

```json
{
  "error": {
    "code": "validation_error",
    "message": "Entrée invalide.",
    "details": [{"field": "area_m2", "message": "Extra inputs are not permitted"}]
  }
}
```

Ces modèles servent à documenter la forme dans OpenAPI ; les réponses sont
construites par `backend.api.errors`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

FIELD_DESCRIPTION = "Chemin du champ refusé (vide si l'erreur n'est pas liée à un champ)."
CODE_DESCRIPTION = (
    "Code stable : validation_error, bad_request, method_not_allowed, not_found, internal_error."
)


class ErrorDetail(BaseModel):
    """Un point de contrat refusé, rattaché au champ concerné."""

    field: str = Field(description=FIELD_DESCRIPTION)
    message: str = Field(description="Motif du refus, tel que formulé par le validateur.")


class ErrorBody(BaseModel):
    """Corps d'erreur unique de l'API."""

    code: str = Field(description=CODE_DESCRIPTION)
    message: str = Field(description="Message lisible, sans détail technique.")
    details: list[ErrorDetail] = Field(
        default_factory=list, description="Détail par champ, quand le refus vient d'une entrée."
    )


class ErrorResponse(BaseModel):
    """Réponse d'erreur complète."""

    error: ErrorBody
