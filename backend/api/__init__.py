"""Application ASGI publique : routes et gestion d'erreurs.

Les routes ne portent pas de logique métier (code-standards §API : « les handlers
restent fins ») : elles valident l'entrée par les schémas et délèguent aux services.
"""

from __future__ import annotations

__all__: list[str] = []
