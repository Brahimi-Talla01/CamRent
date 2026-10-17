"""Configuration et accès technique de l'API (aucun secret en dur).

`config` lit l'environnement à l'appel ; `database` ne construit le moteur
PostgreSQL que lorsque la donnée est réellement nécessaire, ce qui permet à
l'application de démarrer et de répondre sur sa route de santé sans base.
"""

from __future__ import annotations

__all__: list[str] = []
