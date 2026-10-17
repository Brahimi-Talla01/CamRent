"""Schéma de la route de version et de santé."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """État de l'API et version du contrat servi."""

    status: Literal["ok"] = Field(description="`ok` tant que le processus répond.")
    api_version: str = Field(description="Version du contrat d'API.")
    api_prefix: str = Field(description="Préfixe des routes publiques (ex. `/api/v1`).")
