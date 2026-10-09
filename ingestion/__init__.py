"""Ingestion CamRent — collecte des données brutes (Phase 1).

Ce package collecte les sources retenues en Phase 0 et écrit la donnée **brute**
et **immuable** dans `data/raw/`, accompagnée de ses métadonnées et de premières
validations Bronze.

Règle de phase (voir `context/feature-specs/01-data-ingestion.md`) : **aucun
nettoyage ni normalisation** ici — c'est la Phase 2. On capture la donnée telle
qu'observée en préservant les valeurs de source.

Voir `ingestion/README.md` et `docs/phase-1/`.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
