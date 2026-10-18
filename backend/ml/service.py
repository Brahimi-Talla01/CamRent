"""Service d'estimation : estimation indicative + fourchette, sans entraînement.

Domaine servi : le modèle chargé ne connaît que les paires (ville, quartier)
réellement vues à l'entraînement. Hors de ce domaine, le pipeline traiterait
silencieusement la saisie comme « quartier inconnu » (profondeur de marché
nulle, one-hot ignoré) et produirait une estimation faussement plausible : le
service refuse donc explicitement (ticket #51 — « une entrée inconnue produit
une erreur prévisible, jamais une estimation silencieusement fausse »).

La cible transformée `log1p` et la conversion vers les FCFA sont portées par le
pipeline lui-même (Phase 6) : le service ne convertit rien, il ne fait que
demander la prévision et les bornes calibrées à des artefacts déjà entraînés.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.src import config as ml_config
from ml.src.uncertainty import MIN_RENT

from ..schemas.prediction import PredictionRequest, PredictionResponse
from .loader import PinnedModelProvider, ServingBundle, ServingError

# Colonnes d'entrée réellement consommées par le pipeline (source unique : Phase 6).
INPUT_COLUMNS: tuple[str, ...] = ml_config.FEATURE_COLUMNS


def _as_text(value: object) -> str:
    """Texte d'une valeur d'énumération ou d'une chaîne (jamais le nom de la classe).

    `str(CityName.Douala)` donnerait `"CityName.Douala"` : ce sont les **valeurs**
    du vocabulaire qui doivent voyager jusqu'au modèle, pas leurs noms.
    """
    return str(getattr(value, "value", value))


def _scalar(value: object) -> float:
    """Replie une borne (scalaire ou tableau d'une observation) sur un flottant."""
    return float(np.asarray(value, dtype=float).reshape(-1)[0])


class UnknownNeighborhoodError(ValueError):
    """Quartier hors du domaine connu du modèle — traduit en 404 par la route."""

    def __init__(self, city: str, neighborhood: str) -> None:
        super().__init__(f"Quartier inconnu pour {city} : « {neighborhood} ».")
        self.city = city
        self.neighborhood = neighborhood


def known_city_neighborhood_pairs(bundle: ServingBundle) -> set[tuple[str, str]]:
    """Paires (ville, quartier) vues à l'entraînement par le modèle servi.

    La profondeur de marché (`logements_dans_quartier`) est apprise par le
    pipeline lui-même : c'est la même source que celle utilisée pour prédire, ce
    qui interdit toute divergence entre le domaine contrôlé et le domaine servi.

    Raises:
        ServingError: structure du modèle servi inattendue (artefact non conforme).
    """
    try:
        # `TransformedTargetRegressor` clone le pipeline à l'entraînement : c'est
        # la copie ajustée (`regressor_`) qui porte le domaine réellement appris.
        regressor = getattr(bundle.model, "regressor_", None)
        if regressor is None:
            regressor = bundle.model.regressor
        depth = regressor.named_steps["features"].depth_
        return {(str(city), str(neighborhood)) for city, neighborhood in depth.counts_}
    except (AttributeError, KeyError, TypeError) as exc:
        raise ServingError(
            "Modèle servi non conforme : quartiers d'entraînement introuvables."
        ) from exc


class EstimationService:
    """Estime un loyer demandé et sa fourchette à partir du bundle épinglé."""

    def __init__(self, provider: PinnedModelProvider) -> None:
        self._provider = provider
        self._pairs: set[tuple[str, str]] | None = None
        self._pairs_bundle: ServingBundle | None = None

    def _known_pairs(self, bundle: ServingBundle) -> set[tuple[str, str]]:
        """Domaine servi, calculé une seule fois par bundle chargé."""
        if self._pairs_bundle is not bundle:
            self._pairs = known_city_neighborhood_pairs(bundle)
            self._pairs_bundle = bundle
        return self._pairs or set()

    def estimate(self, request: PredictionRequest) -> PredictionResponse:
        """Estimation indicative : prix demandé estimé + fourchette calibrée 5 % / 95 %.

        Reproductible par construction : le bundle épinglé est déterministe et
        aucune stochasticité n'est introduite dans la requête (testée).

        Raises:
            UnknownNeighborhoodError: quartier jamais vu avec cette ville à
                l'entraînement — aucune estimation n'est retournée.
        """
        bundle = self._provider.load()
        city = _as_text(request.city)
        neighborhood = _as_text(request.neighborhood)
        if (city, neighborhood) not in self._known_pairs(bundle):
            raise UnknownNeighborhoodError(city, neighborhood)

        frame = pd.DataFrame(
            [
                {
                    "city": city,
                    "neighborhood": neighborhood,
                    "property_type": _as_text(request.property_type),
                    "bedrooms": request.bedrooms,
                    "bathrooms": request.bathrooms,
                }
            ],
            columns=list(INPUT_COLUMNS),
        )
        estimated = int(round(_scalar(bundle.model.predict(frame))))
        lower_bound, upper_bound = bundle.interval.bounds(frame)
        low, high = sorted((_scalar(lower_bound), _scalar(upper_bound)))
        floor = int(MIN_RENT)
        return PredictionResponse(
            estimated_rent=max(int(round(estimated)), floor),
            currency=ml_config.CURRENCY,
            lower_bound=max(int(round(low)), floor),
            upper_bound=max(int(round(high)), floor),
            model_version=bundle.model_version,
        )
