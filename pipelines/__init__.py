"""Pipelines de transformation CamRent — construction du **Silver dataset**.

Lit le **Raw immuable** (`data/raw/`) et produit des jeux nettoyés et standardisés
dans `data/processed/`, **sans jamais écraser le Raw** ni supprimer une donnée :
les observations invalides vont en **quarantine**.

Voir `context/feature-specs/02-data-cleaning.md` et `pipelines/README.md`.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
