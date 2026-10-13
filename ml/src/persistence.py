"""Sauvegarde du modèle retenu et de ses métadonnées (Phase 6).

Deux fichiers sont écrits dans `ml/models/` (ignoré par git : ce sont des
artefacts régénérables, le livrable versionné reste le rapport) :

- `<nom>.joblib` : le pipeline complet (features + pré-traitement + modèle) ;
- `<nom>.intervalle.joblib` : l'intervalle de prédiction **retenu**, déjà calibré —
  sans lui, une API ne pourrait pas afficher de fourchette sans recalibrer sur le
  mart, ce qui ouvrirait la porte à une calibration sur d'autres données ;
- `<nom>.json` : métadonnées nécessaires pour interpréter/exploiter le modèle
  (features, hyperparamètres, graine, métriques, seuil de référence, intervalle,
  versions).

Le registre de modèles (MLflow, Phase 7) prendra le relais : la structure des
métadonnées est déjà sérialisable telle quelle.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from . import config


def versions() -> dict[str, str]:
    """Versions logicielles utiles à la reproductibilité."""
    result = {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
    }
    try:
        import lightgbm  # noqa: PLC0415

        result["lightgbm"] = lightgbm.__version__
    except ImportError:  # pragma: no cover - dépend de l'environnement
        result["lightgbm"] = "absent"
    return result


def validate_metadata(metadata: dict[str, Any]) -> None:
    """Vérifie que les métadonnées contiennent les clés attendues."""
    missing = [key for key in config.MODEL_METADATA_KEYS if key not in metadata]
    if missing:
        raise ValueError(f"Métadonnées incomplètes : {', '.join(missing)}.")


def save_model(
    estimator: Any,
    metadata: dict[str, Any],
    *,
    models_dir: Path | None = None,
    name: str | None = None,
    interval: Any | None = None,
) -> dict[str, str]:
    """Écrit le modèle, l'intervalle retenu et ses métadonnées ; renvoie les chemins.

    Args:
        estimator: pipeline de prévision (features → pré-traitement → modèle).
        metadata: métadonnées complètes (validées avant écriture).
        interval: intervalle de prédiction **déjà calibré** (optionnel).
    """
    name = config.MODEL_ARTIFACT_NAME if name is None else name
    validate_metadata(metadata)
    models_dir = models_dir or config.MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / f"{name}.joblib"
    metadata_path = models_dir / f"{name}.json"
    joblib.dump(estimator, model_path)
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    paths = {"modele": str(model_path), "metadonnees": str(metadata_path)}
    if interval is not None:
        interval_path = models_dir / f"{name}_intervalle.joblib"
        joblib.dump(interval, interval_path)
        paths["intervalle"] = str(interval_path)
    return paths


def load_model(path: Path) -> Any:
    """Recharge un pipeline sauvegardé (utilisé par les tests et la Phase 8)."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Modèle introuvable : {path}.")
    return joblib.load(path)


def load_interval(path: Path) -> Any:
    """Recharge l'intervalle de prédiction calibré (utilisé par la Phase 8)."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Intervalle introuvable : {path}.")
    return joblib.load(path)


def load_metadata(path: Path) -> dict[str, Any]:
    """Recharge les métadonnées d'un modèle."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Métadonnées introuvables : {path}.")
    return json.loads(Path(path).read_text(encoding="utf-8"))
