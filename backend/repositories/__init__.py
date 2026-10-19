"""Accès PostgreSQL aux marts de la plateforme data.

Les lectures se font sur les marts dbt (`analytics_marts.*` par défaut), jamais sur
les tables d'atterrissage ni sur les données brutes : le backend ne rejoue pas la
transformation. `market` expose les statistiques avec leur nombre d'observations
(ticket #53) ; le schéma se règle par `DBT_MARTS_SCHEMA`.
"""

from __future__ import annotations

__all__: list[str] = []
