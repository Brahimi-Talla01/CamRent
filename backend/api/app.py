"""Application ASGI de l'API publique (spec 08, ticket #50).

Point d'entrée de développement : `uvicorn backend.api.app:app --reload`.

Le socle (#50) pose l'application versionnée, les schémas stricts, les erreurs au
format unique et la route de santé ; l'endpoint de prédiction (#51), les routes de
marché (#53) et la comparaison (#54) forment l'API publique du sous-système
Estimation. L'API interne du back-office (#61) est une **application distincte**,
jamais une route de celle-ci (spec 08 §Scope Limits).
"""

from __future__ import annotations

from fastapi import FastAPI

from ..infrastructure import config
from .errors import register_error_handlers
from .routes import comparisons, health, market, predictions


def create_app() -> FastAPI:
    """Construit l'application : routes, contrat OpenAPI et gestion d'erreurs."""
    app = FastAPI(
        title=config.API_TITLE,
        version=config.API_VERSION,
        description=(
            "API publique de CamRent : estimation indicative du loyer mensuel **demandé** "
            "dans les annonces (Yaoundé et Douala) et statistiques de marché. "
            "Une estimation n'est jamais une valeur officielle du bien."
        ),
    )
    register_error_handlers(app)
    app.include_router(health.router, prefix=config.API_PREFIX, tags=["santé"])
    app.include_router(
        predictions.router, prefix=config.API_PREFIX, tags=["prédiction"]
    )
    app.include_router(market.router, prefix=config.API_PREFIX, tags=["marché"])
    app.include_router(
        comparisons.router, prefix=config.API_PREFIX, tags=["comparaison"]
    )
    return app


app = create_app()
