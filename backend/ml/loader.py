"""Chargement du modèle épinglé et de son intervalle (ticket #51, spec 08 §5).

Le serving ne s'entraîne jamais dans une requête : il charge la version
consignée dans `ml/models/champion.json` (Phase 7, lot A2) et refuse
explicitement de servir si cette version ou son intervalle calibré sont
indisponibles — jamais d'estimation sans fourchette, jamais de fourchette
improvisée.

Deux sources, tranchées par le porteur du projet (2026-10-17) :

- le **modèle** vient du registre MLflow, à l'URI épinglée dans le fichier de
  pin (`model_uri`) : aucun fichier de modèle local implicite ;
- la **fourchette** (régression quantile 5 % / 95 %, déjà calibrée en Phase 6)
  vient de l'artefact local `ml/models/rent_model_v1_intervalle.joblib`,
  régénérable par `python -m ml.src models`. Ce fichier n'est pas versionné :
  son absence est une erreur explicite, jamais contournée (couplage documenté
  dans `docs/phase-8/README.md`).

Aucun secret n'est lu ici : l'URI de suivi MLflow suit les mêmes règles que la
Phase 7 (`MLFLOW_TRACKING_URI`, sinon base dérivée de `DATABASE_URL`), et les
messages d'erreur nomment les fichiers, jamais d'identifiants.
"""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ml.src import config as ml_config

logger = logging.getLogger(__name__)

# Clés minimales sans lesquelles le pin ne désigne pas une version servable.
REQUIRED_PIN_KEYS: tuple[str, ...] = ("etiquette", "model_uri")


class ServingError(RuntimeError):
    """Le service d'estimation est indisponible (réponse servie : 500 générique)."""


def champion_pin_path() -> Path:
    """Chemin du fichier **versionné** qui épingle la version servie."""
    return ml_config.CHAMPION_PIN_PATH


def interval_path() -> Path:
    """Chemin de l'intervalle calibré (artefact Phase 6, régénérable, non versionné)."""
    return ml_config.MODELS_DIR / f"{ml_config.MODEL_ARTIFACT_NAME}_intervalle.joblib"


def read_champion_pin(path: Path | None = None) -> dict[str, Any]:
    """Relit la version épinglée ; échec explicite si elle est absente ou illisible.

    Args:
        path: chemin du pin (défaut : `ml/models/champion.json`).

    Raises:
        ServingError: fichier absent, illisible ou incomplet — aucune prédiction
            n'est servie sans provenance épinglée.
    """
    pin_path = Path(path) if path is not None else champion_pin_path()
    if not pin_path.is_file():
        raise ServingError(
            f"Version épinglée introuvable : {pin_path}. Relancer la Phase 7 "
            "(`python -m ml.src registry`) pour épingler le modèle servi."
        )
    try:
        payload = json.loads(pin_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ServingError(f"Version épinglée illisible : {pin_path}.") from exc
    if not isinstance(payload, dict):
        raise ServingError(f"Version épinglée illisible (format inattendu) : {pin_path}.")
    missing = [key for key in REQUIRED_PIN_KEYS if not payload.get(key)]
    if missing:
        raise ServingError(f"Version épinglée incomplète ({', '.join(missing)}) : {pin_path}.")
    return payload


def load_model_from_registry(pin: dict[str, Any]) -> Any:
    """Charge le pipeline à l'URI épinglée du registre MLflow.

    L'import de MLflow est paresseux : l'application démarre et sert la santé
    sans que la dépendance ne soit chargée.
    """
    try:
        import mlflow
        import mlflow.sklearn

        from ml.src import tracking
    except ImportError as exc:  # pragma: no cover - extra `ml` installé dans la CI
        raise ServingError(
            "Dépendance MLflow absente (extra `ml`) : modèle épinglé injoignable."
        ) from exc
    mlflow.set_tracking_uri(tracking.resolve_tracking_uri())
    try:
        return mlflow.sklearn.load_model(str(pin["model_uri"]))
    except Exception as exc:  # frontière de serving : échec explicite, jamais silencieux
        logger.error("Chargement du modèle épinglé échoué (%s)", type(exc).__name__)
        raise ServingError(
            f"Modèle épinglé injoignable ({pin.get('etiquette')}) : registre MLflow "
            "injoignable ou artefacts absents."
        ) from exc


def load_interval(path: Path | None = None) -> Any:
    """Charge l'intervalle quantile déjà calibré (artefact Phase 6).

    La fourchette n'est jamais improvisée : sans cet artefact, le modèle servi
    n'a pas sa fourchette calibrée et l'API refuse de répondre.
    """
    artifact = Path(path) if path is not None else interval_path()
    if not artifact.is_file():
        raise ServingError(
            f"Intervalle de prédiction introuvable : {artifact}. Rejouer "
            "`python -m ml.src models` pour régénérer la fourchette calibrée."
        )
    try:
        import joblib

        return joblib.load(artifact)
    except Exception as exc:  # frontière de serving : échec explicite, jamais silencieux
        logger.error("Chargement de l'intervalle échoué (%s)", type(exc).__name__)
        raise ServingError(f"Intervalle de prédiction illisible : {artifact}.") from exc


@dataclass(frozen=True)
class ServingBundle:
    """Ce qui est nécessaire pour servir une estimation, sans dérive possible."""

    pin: dict[str, Any]
    model: Any
    interval: Any

    @property
    def model_version(self) -> str:
        """Version servie, telle qu'épinglée — publiée dans chaque réponse."""
        return str(self.pin["etiquette"])


ModelLoader = Callable[[dict[str, Any]], Any]
IntervalLoader = Callable[[], Any]


class PinnedModelProvider:
    """Charge le bundle épinglé une seule fois, puis le met en cache.

    Les chargeurs sont injectables : les tests et la CI exercent le vrai service
    sans registre MLflow ni artefact du poste local.
    """

    def __init__(
        self,
        *,
        pin_path: Path | None = None,
        model_loader: ModelLoader | None = None,
        interval_loader: IntervalLoader | None = None,
    ) -> None:
        self._pin_path = pin_path
        self._model_loader = model_loader
        self._interval_loader = interval_loader
        self._bundle: ServingBundle | None = None
        self._lock = threading.Lock()

    def load(self) -> ServingBundle:
        """Retourne le bundle épinglé (chargé au premier appel, verrouillé)."""
        if self._bundle is not None:
            return self._bundle
        with self._lock:
            if self._bundle is None:
                pin = read_champion_pin(self._pin_path)
                model = (self._model_loader or load_model_from_registry)(pin)
                interval = (self._interval_loader or load_interval)()
                self._bundle = ServingBundle(pin=pin, model=model, interval=interval)
        return self._bundle
