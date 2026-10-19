"""Route de comparaison : `POST /api/v1/comparisons` (ticket #54, spec 08 §4).

La route est fine : contrat Pydantic strict, délégation au service, traduction
de l'erreur de domaine en 404. Elle **réutilise les dépendances** des deux
endpoints déjà livrés (`get_estimation_service`, `get_market_service`) : la
comparaison ne peut donc pas calculer une estimation ou un groupe de marché
différent de `/predictions` et `/market/prices`.

Le handler est synchrone : la lecture PostgreSQL est bloquante et FastAPI
l'exécute dans son pool de threads.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...ml.service import EstimationService, UnknownNeighborhoodError
from ...schemas.comparison import ComparisonRequest, ComparisonResponse
from ...services.comparison import ComparisonService
from ...services.market import MarketService
from .market import get_market_service
from .predictions import get_estimation_service

router = APIRouter()

DESCRIPTION = (
    "Confronte le loyer **demandé** d'un logement à l'estimation du modèle épinglé "
    "et au marché local (moyenne, médiane, nombre d'observations). L'écart est "
    "signé (`asking_rent - référence`) : positif, le prix demandé est au-dessus de "
    "la référence. La médiane sous le seuil de publication reste absente. Aucun "
    "score de confiance ni recommandation : l'API informe, elle ne certifie pas une "
    "valeur officielle."
)


def get_comparison_service(
    estimation: Annotated[EstimationService, Depends(get_estimation_service)],
    market: Annotated[MarketService, Depends(get_market_service)],
) -> ComparisonService:
    """Service de comparaison composé des briques prédiction et marché."""
    return ComparisonService(estimation, market)


@router.post(
    "/comparisons",
    response_model=ComparisonResponse,
    summary="Compare un ou plusieurs loyers demandés au marché local",
    description=DESCRIPTION,
)
def create_comparisons(
    payload: ComparisonRequest,
    service: Annotated[ComparisonService, Depends(get_comparison_service)],
) -> ComparisonResponse:
    """Compare chaque logement à l'estimation et au groupe de marché local.

    Un quartier jamais vu par le modèle est refusé en 404, comme pour
    `/predictions` : aucune estimation, donc aucune comparaison inventée. Un
    groupe de marché absent produit `market: null`, pas une référence élargie.
    """
    try:
        return service.compare(payload)
    except UnknownNeighborhoodError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
