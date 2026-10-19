"""Champs partagés par les schémas de l'API publique.

Le quartier est une chaîne libre côté annonce : on retire les espaces superflus
et on refuse une valeur vide, sans transformer le libellé. La reconnaissance du
quartier est vérifiée par le service (prédiction) ou signalée par les marts
(marché), jamais inventée au niveau du schéma.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import StringConstraints

from ..domain import vocabulary

Neighborhood = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=vocabulary.NEIGHBORHOOD_MAX_LENGTH,
    ),
]
