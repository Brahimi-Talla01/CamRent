"""Route de version et de santé.

Elle ne touche ni la base ni le modèle : elle dit quel contrat d'API est servi, ce
qui est vérifiable sans dépendance externe et permet de contrôler un déploiement
avant de l'interroger sur des données.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...infrastructure import config
from ...schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Version et état de l'API",
    description="Indique le contrat servi (`/api/v1`) ; ne lit ni la base ni le modèle.",
)
async def read_health() -> HealthResponse:
    """Retourne l'état de l'API et la version de son contrat."""
    return HealthResponse(
        status="ok",
        api_version=config.API_VERSION,
        api_prefix=config.API_PREFIX,
    )
