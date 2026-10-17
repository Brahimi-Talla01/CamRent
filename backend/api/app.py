"""Application ASGI de l'API publique (spec 08, ticket #50).

Point d'entrée de développement : `uvicorn backend.api.app:app --reload`.

Le ticket #50 pose le socle : application versionnée, schémas stricts, erreurs au
format unique, route de santé. Aucun endpoint métier n'est exposé ici — les routes
de prédiction, de marché et de comparaison arrivent avec #51, #53 et #54, et l'API
interne du back-office (#61) est une **application distincte**, jamais une route de
celle-ci (spec 08 §Scope Limits).
"""

from __future__ import annotations

from fastapi import FastAPI

from ..infrastructure import config
from .errors import register_error_handlers
from .routes import health


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
    return app


app = create_app()
