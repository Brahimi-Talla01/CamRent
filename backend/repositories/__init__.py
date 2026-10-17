"""Accès PostgreSQL aux marts de la plateforme data.

Les lectures se font sur les marts dbt (`analytics_marts.*`), jamais sur les tables
d'atterrissage ni sur les données brutes : le backend ne rejoue pas la
transformation. Les statistiques de marché — qui exigent toujours leur nombre
d'observations — arrivent avec le ticket #53.
"""

from __future__ import annotations

__all__: list[str] = []
