"""Fixtures partagées des tests unitaires.

Le dataset synthétique de la Phase 5 est construit ici : il reproduit le schéma
de `analytics_marts.mart_ml_dataset` avec des prix choisis pour que les médianes
attendues soient calculables à la main.
"""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def ml_frame() -> pd.DataFrame:
    """6 observations : 2 villes, 3 quartiers, 2 types, prix connus.

    Médianes attendues :
    - par ville : Douala 200 000 (5 obs), Yaoundé 500 000 (1 obs) ;
    - par (ville, quartier, type) : Bali/appartement 150 000, Makepe/appartement
      350 000, Bastos/appartement 500 000, Bali/studio 50 000.
    """
    rows = [
        ("l1", "Douala", "Bali", "apartment", 2, 2, 100_000, False, False, ""),
        ("l2", "Douala", "Bali", "apartment", 3, 2, 200_000, False, True, ""),
        ("l3", "Douala", "Bali", "studio", 1, 1, 50_000, True, False, ""),
        ("l4", "Douala", "Makepe", "apartment", 2, 2, 300_000, False, False, ""),
        ("l5", "Douala", "Makepe", "apartment", 2, 1, 400_000, False, False, ""),
        ("l6", "Yaoundé", "Bastos", "apartment", 3, 3, 500_000, True, False, "prix_extreme"),
    ]
    frame = pd.DataFrame(
        rows,
        columns=[
            "listing_key",
            "city",
            "neighborhood",
            "property_type",
            "bedrooms",
            "bathrooms",
            "target_rent_price",
            "price_is_bound",
            "is_republication",
            "outlier_flags",
        ],
    )
    frame["neighborhood_recognized"] = frame["neighborhood"].isin(
        ["Bali", "Makepe", "Bastos"]
    )
    frame["collected_at"] = "2026-10-09T07:05:36+00:00"
    frame["posted_at"] = None
    return frame
