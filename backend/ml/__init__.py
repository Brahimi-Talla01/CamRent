"""Chargement du modèle servi par l'API publique.

Le serving lit la version **épinglée** (`ml/models/champion.json`, Phase 7) et ne
s'entraîne jamais dans une requête (spec 08 §Scope Limits). Le chargement, la
fourchette et la fiabilité du pin arrivent avec les tickets #51 et #52 ; ce paquet
tient cette responsabilité hors des routes et des services métier.
"""

from __future__ import annotations

__all__: list[str] = []
