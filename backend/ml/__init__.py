"""Chargement du modèle servi par l'API publique.

Le serving lit la version **épinglée** (`ml/models/champion.json`, Phase 7) et ne
s'entraîne jamais dans une requête (spec 08 §Scope Limits). `loader` charge le
bundle épinglé (modèle du registre + fourchette calibrée, en cache, échec
explicite) ; `service` produit l'estimation et refuse le hors-domaine. La
fiabilité du pin face au mart vivant relève du ticket #52.
"""

from __future__ import annotations

__all__: list[str] = []
