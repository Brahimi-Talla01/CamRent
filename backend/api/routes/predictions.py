"""Route d'estimation : `POST /api/v1/predictions` (ticket #51, spec 08 §2).

La route reste fine : validation d'entrée par le schéma strict, délégation au
service d'estimation, traduction des erreurs métier vers le format unique.
Le modèle est chargé au premier appel utile (cache), jamais à l'import —
l'application démarre et sert la santé sans registre ni artefact joignables.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...ml.loader import PinnedModelProvider
from ...ml.service import EstimationService, UnknownNeighborhoodError
from ...schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter()

# Provider partagé de l'application : le bundle épinglé est chargé une fois.
_provider = PinnedModelProvider()

DESCRIPTION = (
    "Estimation indicative du loyer mensuel **demandé** issue du modèle épinglé "
    "(`ml/models/champion.json`), avec fourchette calibrée 5 % / 95 % (Phase 6). "
    "Une estimation reflète les prix observés dans les annonces : ce n'est jamais "
    "la valeur officielle du bien."
)


def get_estimation_service() -> EstimationService:
    """Service d'estimation de l'application (modèle épinglé, mis en cache)."""
    return EstimationService(_provider)


@router.post(
    "/predictions",
    response_model=PredictionResponse,
    summary="Estimation indicative du loyer mensuel demandé",
    description=DESCRIPTION,
)
async def create_prediction(
    payload: PredictionRequest,
    service: Annotated[EstimationService, Depends(get_estimation_service)],
) -> PredictionResponse:
    """Estime un loyer demandé pour les caractéristiques saisies.

    Une ville ou un type de bien hors vocabulaire est refusé par le schéma
    (422) ; un quartier jamais vu avec cette ville à l'entraînement est refusé
    en 404 — jamais une estimation silencieusement fausse.
    """
    try:
        return service.estimate(payload)
    except UnknownNeighborhoodError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
