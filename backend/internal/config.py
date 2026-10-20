"""Constantes du contrat de l'API interne (08b.1), sans secret ni chemin en dur.

Les valeurs ici sont **stables** (contrat, bornes) ; tout ce qui dépend de
l'environnement est lu par `backend/internal/settings.py`.
"""

from __future__ import annotations

from typing import Final

# Version du contrat, à ne pas confondre avec la version du modèle servi
# (`ml/models/champion.json`, Phase 7).
API_VERSION: Final[str] = "0.1.0"
API_PREFIX: Final[str] = "/internal/api/v1"

# Durée de vie d'un jeton d'accès (heures). Surchargeable par
# `INTERNAL_TOKEN_TTL_HOURS` ; la session interne n'est pas éternelle.
DEFAULT_TOKEN_TTL_HOURS: Final[int] = 12

# Longueur minimale d'un mot de passe de compte interne. Volontairement élevée :
# ces comptes accèdent aux sources, aux jobs et au registre des modèles.
MIN_PASSWORD_LENGTH: Final[int] = 12

# Pagination du journal d'audit.
AUDIT_DEFAULT_LIMIT: Final[int] = 50
AUDIT_MAX_LIMIT: Final[int] = 200
