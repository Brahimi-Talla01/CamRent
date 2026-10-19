"""Routes de marché : `GET /api/v1/market/{cities,neighborhoods,prices}`.

La route reste fine : validation des paramètres par FastAPI/Pydantic, délégation
au service, traduction des erreurs métier au format unique de l'API. Aucune
statistique n'est calculée ici — les marts sont la seule source.

Les handlers sont **synchrones** : la lecture PostgreSQL est bloquante et
FastAPI l'exécute dans son pool de threads, sans immobiliser la boucle ASGI.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ...domain import vocabulary
from ...infrastructure import config
from ...repositories.market import PostgresMarketRepository
from ...schemas.common import Neighborhood
from ...schemas.market import CitiesResponse, NeighborhoodsResponse, PricesResponse
from ...services.market import (
    InvalidMarketFilterError,
    MarketService,
    PeriodFilterUnavailableError,
)

router = APIRouter()

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

ROOMS_DESCRIPTION = "Nombre de chambres (bornes de la plateforme data)."


def _rooms_query() -> Query:
    """Bornes de chambres, sans valeur par défaut (elle reste portée par `=`)."""
    return Query(
        ge=vocabulary.ROOMS_MIN,
        le=vocabulary.ROOMS_MAX,
        description=ROOMS_DESCRIPTION,
    )


@lru_cache(maxsize=4)
def _repository(database_url: str, schema: str) -> PostgresMarketRepository:
    """Dépôt partagé par configuration : un pool de connexions par base/schéma."""
    return PostgresMarketRepository(database_url, schema=schema)


def get_market_service() -> MarketService:
    """Service de marché de l'application (base et schéma lus à l'appel)."""
    return MarketService(
        _repository(config.database_url(), config.market_marts_schema())
    )


@router.get(
    "/market/cities",
    response_model=CitiesResponse,
    summary="Villes disponibles et volumes d'observations",
    description=(
        "Statistiques par ville issues de `mart_city_prices` : chaque ligne porte "
        "son nombre d'observations, sa fourchette p10/p90 et la part de prix "
        "bornés et de republications. Aucune ville sans données n'est inventée."
    ),
)
def list_cities(
    service: Annotated[MarketService, Depends(get_market_service)],
) -> CitiesResponse:
    """Villes du MVP avec leurs statistiques agrégées."""
    return service.cities()


@router.get(
    "/market/neighborhoods",
    response_model=NeighborhoodsResponse,
    summary="Quartiers d'une ville et leur volume d'observations",
    description=(
        "Synthèse par quartier construite depuis `mart_neighborhood_prices` : "
        "total d'observations, moyenne pondérée, minimum, maximum et biais connus. "
        "La médiane n'est pas agrégée ici (agréger des médianes n'aurait pas de "
        "sens) ; le détail par type et chambres, avec le seuil de publication, "
        "est disponible via `/market/prices`."
    ),
)
def list_neighborhoods(
    city: Annotated[vocabulary.CityName, Query(description="Ville interrogée.")],
    service: Annotated[MarketService, Depends(get_market_service)],
    property_type: Annotated[
        vocabulary.PropertyType | None,
        Query(description="Restreint aux groupes de ce type de bien."),
    ] = None,
    bedrooms: Annotated[int | None, _rooms_query()] = None,
) -> NeighborhoodsResponse:
    """Quartiers d'une ville, filtrables par type et nombre de chambres."""
    return service.neighborhoods(
        city=city.value, property_type=None if property_type is None else property_type.value,
        bedrooms=bedrooms,
    )


@router.get(
    "/market/prices",
    response_model=PricesResponse,
    summary="Statistiques de prix selon les filtres",
    description=(
        "Groupes de prix issus des marts de marché. Chaque groupe porte son nombre "
        "d'observations et ses dimensions ; la médiane n'est renseignée qu'à partir "
        "du seuil de publication (`min_publish_n`), sinon `median_published` vaut "
        "`false`. Un filtre sans résultat renvoie une liste vide explicite, jamais "
        "une statistique inventée."
    ),
)
def get_prices(
    service: Annotated[MarketService, Depends(get_market_service)],
    city: Annotated[
        vocabulary.CityName | None, Query(description="Ville (toutes si omise).")
    ] = None,
    neighborhood: Annotated[
        Neighborhood | None,
        Query(description="Quartier ; exige `city`."),
    ] = None,
    property_type: Annotated[
        vocabulary.PropertyType | None, Query(description="Type de bien.")
    ] = None,
    bedrooms: Annotated[int | None, _rooms_query()] = None,
    period: Annotated[
        str | None,
        Query(
            pattern=PERIOD_PATTERN,
            description=(
                "Mois observé (`YYYY-MM`). Les marts actuels couvrent une seule "
                "période ; tout autre mois renvoie une réponse vide explicite."
            ),
        ),
    ] = None,
) -> PricesResponse:
    """Groupes de prix correspondant aux filtres, avec leur N et leur qualité."""
    try:
        return service.prices(
            city=None if city is None else city.value,
            neighborhood=neighborhood,
            property_type=None if property_type is None else property_type.value,
            bedrooms=bedrooms,
            period=period,
        )
    except (InvalidMarketFilterError, PeriodFilterUnavailableError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
