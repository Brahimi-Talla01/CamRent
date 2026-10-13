"""Baselines de référence (Phase 5).

Trois baselines mesurables, sans modèle complexe ni hyperparamètre :

- `baseline_global` — moyenne globale des prix d'entraînement ;
- `baseline_city` — médiane par ville ;
- `baseline_neighborhood` — médiane par (ville, quartier, type de logement).

Une baseline de groupe ne peut pas prédire un groupe jamais vu à
l'entraînement : chacune porte donc une **chaîne de repli** explicite
(`ville + type` → `ville` → `moyenne globale`) et chaque prédiction est
étiquetée par le niveau qui l'a produite, ce qui rend le taux de repli
mesurable dans le rapport (aucun repli silencieux).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy as np
import pandas as pd

from . import config


@runtime_checkable
class Baseline(Protocol):
    """Contrat minimal d'une baseline : `fit` sur l'entraînement, `predict` ensuite."""

    name: str

    def fit(self, frame: pd.DataFrame) -> Baseline: ...

    def predict(self, frame: pd.DataFrame) -> np.ndarray: ...

    def predict_with_levels(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]: ...

    def describe(self) -> dict[str, Any]: ...


class GlobalMeanBaseline:
    """Moyenne globale des prix : la baseline la plus naïve."""

    name = "baseline_global"
    definition = "moyenne des prix d'entraînement"

    def __init__(self) -> None:
        self._mean: float | None = None

    def fit(self, frame: pd.DataFrame) -> GlobalMeanBaseline:
        if frame.empty:
            raise ValueError("Impossible d'entraîner une baseline sur un dataset vide.")
        target = frame[config.TARGET].astype(float)
        if target.isna().any():
            raise ValueError("La cible contient des valeurs manquantes à l'entraînement.")
        self._mean = float(target.mean())
        return self

    def predict_with_levels(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        if self._mean is None:
            raise RuntimeError("La baseline doit être entraînée (`fit`) avant `predict`.")
        values = np.full(len(frame), self._mean, dtype=float)
        levels = np.full(len(frame), self.name, dtype=object)
        return values, levels

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return self.predict_with_levels(frame)[0]

    def describe(self) -> dict[str, Any]:
        return {
            "nom": self.name,
            "definition": self.definition,
            "groupes": 1,
            "valeur_apprise": None if self._mean is None else round(self._mean),
        }


class GroupMedianBaseline:
    """Médiane par groupe de clés, avec repli explicite sur une autre baseline."""

    def __init__(
        self,
        keys: tuple[str, ...],
        *,
        name: str | None = None,
        definition: str | None = None,
        fallback: Baseline | None = None,
    ) -> None:
        if not keys:
            raise ValueError("Au moins une clé de regroupement est requise.")
        self.keys = keys
        self.name = name or "baseline_" + "_".join(keys)
        self.definition = definition or f"médiane par {', '.join(keys)}"
        self.fallback = fallback
        self._medians: dict[tuple[Any, ...], float] = {}
        self._counts: dict[tuple[Any, ...], int] = {}
        self._global_median: float | None = None

    def _as_tuple(self, key: Any) -> tuple[Any, ...]:
        return key if isinstance(key, tuple) else (key,)

    def fit(self, frame: pd.DataFrame) -> GroupMedianBaseline:
        if frame.empty:
            raise ValueError("Impossible d'entraîner une baseline sur un dataset vide.")
        grouped = frame.groupby(list(self.keys), dropna=False)[config.TARGET].agg(
            ["median", "count"]
        )
        self._medians = {
            self._as_tuple(key): float(row["median"]) for key, row in grouped.iterrows()
        }
        self._counts = {
            self._as_tuple(key): int(row["count"]) for key, row in grouped.iterrows()
        }
        self._global_median = float(frame[config.TARGET].astype(float).median())
        if self.fallback is not None:
            self.fallback.fit(frame)
        return self

    def predict_with_levels(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        if not self._medians:
            raise RuntimeError("La baseline doit être entraînée (`fit`) avant `predict`.")
        rows = list(zip(*(frame[key] for key in self.keys), strict=True))
        values = np.full(len(frame), np.nan, dtype=float)
        levels = np.full(len(frame), self.name, dtype=object)
        missing: list[int] = []
        for position, key in enumerate(rows):
            median = self._medians.get(self._as_tuple(key))
            if median is None:
                missing.append(position)
            else:
                values[position] = median

        if missing:
            if self.fallback is None:
                raise RuntimeError(
                    f"{self.name} : {len(missing)} ligne(s) hors des groupes vus à "
                    "l'entraînement et aucun repli n'est défini."
                )
            positions = np.asarray(missing, dtype=int)
            sub_values, sub_levels = self.fallback.predict_with_levels(
                frame.iloc[positions].reset_index(drop=True)
            )
            values[positions] = sub_values
            levels[positions] = sub_levels
        return values, levels

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return self.predict_with_levels(frame)[0]

    def describe(self) -> dict[str, Any]:
        counts = list(self._counts.values())
        return {
            "nom": self.name,
            "definition": self.definition,
            "cles": list(self.keys),
            "groupes": len(self._medians),
            "observations_min_par_groupe": min(counts) if counts else None,
            "observations_medianes_par_groupe": (
                int(np.median(counts)) if counts else None
            ),
            "repli": self.fallback.name if self.fallback is not None else None,
            "valeur_apprise": (
                None if self._global_median is None else round(self._global_median)
            ),
        }


def build_baselines() -> list[Baseline]:
    """Construit les trois baselines de la spec, dans l'ordre d'évaluation.

    `baseline_city_type` n'est pas une baseline de la spec : elle sert de niveau
    intermédiaire de repli pour `baseline_neighborhood` afin qu'un couple
    (quartier, type) jamais vu retombe d'abord sur sa ville **et** son type.
    """
    global_baseline = GlobalMeanBaseline()
    city_baseline = GroupMedianBaseline(
        ("city",),
        name="baseline_city",
        definition="médiane par ville",
        fallback=global_baseline,
    )
    city_type_baseline = GroupMedianBaseline(
        ("city", "property_type"),
        name="baseline_city_type",
        definition="médiane par ville et type de logement (niveau de repli)",
        fallback=city_baseline,
    )
    neighborhood_baseline = GroupMedianBaseline(
        ("city", "neighborhood", "property_type"),
        name="baseline_neighborhood",
        definition="médiane par (ville, quartier, type de logement)",
        fallback=city_type_baseline,
    )
    return [global_baseline, city_baseline, neighborhood_baseline]
