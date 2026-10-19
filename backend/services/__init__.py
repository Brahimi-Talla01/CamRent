"""Logique métier de l'API publique (estimation, marché, comparaison).

La logique d'estimation vit dans `backend/ml/` (chargement du bundle épinglé et
estimation, ticket #51) ; `market` assemble les réponses des marts (#53) et
`comparison` (#54) réutilise ces deux briques sans recalcul. Ce paquet existe
pour que la logique ne se retrouve jamais dans les routes.
"""

from __future__ import annotations

__all__: list[str] = []
