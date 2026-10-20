"""API interne du back-office CamRent (Phase 8b, ticket #61).

Application **distincte** de l'API publique FastAPI (`backend/api/`) : elle
authentifie ses appelants, réserve ses routes aux rôles internes (`admin` au
départ) et journalise les actions sensibles. Point d'entrée ASGI :
`uvicorn backend.internal.asgi:application`, gestion :
`python manage.py ...`.
"""

from __future__ import annotations

__all__ = ["__version__"]

# Version du **contrat** de l'API interne, pas une version logicielle du produit.
__version__ = "0.1.0"
