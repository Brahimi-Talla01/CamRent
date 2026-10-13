"""Séparation train / validation / test (Phase 5).

Séparation **aléatoire stratifiée par rien** mais **déterministe** : la graine
est fixe et documentée, donc un même dataset produit toujours les mêmes
ensembles. La séparation chronologique n'est pas possible : `posted_at` est vide
dans le Silver et `collected_at` couvre une seule journée (cf. `describe_chronology`).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def split_dataset(
    frame: pd.DataFrame,
    *,
    shares: dict[str, float] | None = None,
    seed: int | None = None,
) -> dict[str, pd.DataFrame]:
    """Découpe `frame` en ensembles disjoints reproductibles.

    Args:
        frame: dataset complet (aucune ligne n'est écartée).
        shares: proportions par ensemble (défaut : `config.SPLIT_SHARES`).
        seed: graine aléatoire (défaut : `config.RANDOM_SEED`).

    Returns:
        Dictionnaire `{"train": ..., "validation": ..., "test": ...}` dans
        l'ordre de `shares`. Les arrondis sont absorbés par l'entraînement pour
        que la somme des tailles soit exactement `len(frame)`.

    Raises:
        ValueError: proportions invalides ou dataset trop petit.
    """
    shares = dict(config.SPLIT_SHARES if shares is None else shares)
    if not shares:
        raise ValueError("Au moins un ensemble est requis.")
    if any(share <= 0 for share in shares.values()):
        raise ValueError(f"Chaque proportion doit être strictement positive : {shares}.")
    total = sum(shares.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"Les proportions doivent sommer à 1 (obtenu : {total}).")

    size = len(frame)
    first = next(iter(shares))
    if size < len(shares):
        raise ValueError(f"Dataset trop petit ({size} lignes) pour {len(shares)} ensembles.")

    rng = np.random.default_rng(config.RANDOM_SEED if seed is None else seed)
    order = rng.permutation(size)

    sizes = {name: int(round(share * size)) for name, share in shares.items()}
    sizes[first] += size - sum(sizes.values())

    parts: dict[str, pd.DataFrame] = {}
    start = 0
    for name in shares:
        stop = start + sizes[name]
        parts[name] = frame.iloc[order[start:stop]].reset_index(drop=True)
        start = stop
    return parts
