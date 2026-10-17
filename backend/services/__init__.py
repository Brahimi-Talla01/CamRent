"""Logique métier de l'API publique (estimation, marché, comparaison).

La logique d'estimation vit dans `backend/ml/` (chargement du bundle épinglé et
estimation, ticket #51) — ce paquet accueillera les services de marché (#53) et
de comparaison (#54). Il existe pour que la logique ne se retrouve jamais dans les
routes.
"""

from __future__ import annotations

__all__: list[str] = []
