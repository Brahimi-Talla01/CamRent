"""Application ASGI de l'API publique (spec 08, ticket #50).

Point d'entrée de développement : `uvicorn backend.api.app:app --reload`.

Le socle (#50) pose l'application versionnée, les schémas stricts, les erreurs au
format unique et la route de santé ; l'endpoint de prédiction (#51) rejoint le
sous-système Estimation. Les routes de marché (#53) et de comparaison (#54)
suivent, et l'API interne du back-office (#61) est une **application distincte**,
jamais une route de celle-ci (spec 08 §Scope Limits).
"""

from __future__ import annotations

from fastapi import FastAPI

from ..infrastructure import config
from .errors import register_error_handlers
from .routes import health, predictions


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
    return app


app = create_app()
