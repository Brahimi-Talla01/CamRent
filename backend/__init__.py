"""Backend de CamRent — sous-systèmes Estimation et Back-office.

Le paquet est découpé selon la spec 08 §1, pour que les routes restent fines et que
chaque responsabilité ait un seul endroit :

- `api/` — application ASGI publique, routes et gestion d'erreurs ;
- `schemas/` — contrat d'entrée/sortie (Pydantic) ;
- `domain/` — vocabulaire et règles du domaine, sans dépendance technique ;
- `services/` — logique métier (estimation, marché, comparaison) ;
- `repositories/` — accès PostgreSQL aux marts de la plateforme data ;
- `ml/` — chargement du modèle épinglé (`ml/models/champion.json`, Phase 7) ;
- `infrastructure/` — configuration et accès base, sans secret en dur.

Le ticket #50 livre le socle (routes de santé, schémas stricts, erreurs) ; les
endpoints publics arrivent avec #51 (prédiction), #53 (marché) et #54 (comparaison),
l'API interne du back-office avec #61.
"""

from __future__ import annotations

__all__: list[str] = []
