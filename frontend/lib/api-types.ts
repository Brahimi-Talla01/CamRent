/**
 * Types du contrat de l'API publique (Phase 08a).
 *
 * Seuls les champs **consommés à l'écran** sont repris ici : ces types
 * reflètent `backend/schemas/{prediction,market}.py` pour ce que le frontend
 * lit. La référence reste le schéma du backend — ce fichier ne le généralise
 * jamais à l'aveugle.
 */

/** Réponse de `POST /api/v1/predictions` (ticket #51). */
export type PredictionResponse = {
  /** Loyer mensuel demandé estimé en FCFA (valeur indicative). */
  estimated_rent: number;
  currency: "XAF";
  /** Borne basse de la fourchette calibrée (5ᵉ percentile, Phase 6). */
  lower_bound: number;
  /** Borne haute de la fourchette calibrée (95ᵉ percentile, Phase 6). */
  upper_bound: number;
  /** Version du modèle épinglée (`ml/models/champion.json`). */
  model_version: string;
};

/** Caractéristiques du formulaire : les seules prises en charge par le modèle. */
export type PredictionRequest = {
  city: string;
  neighborhood: string;
  property_type: string;
  bedrooms: number;
  bathrooms: number;
};

/** Statistiques d'un groupe de marché — `backend/schemas/market.py`. */
export type MarketStats = {
  n_observations: number;
  mean_rent_price: number;
  median_rent_price: number | null;
  median_published: boolean;
  p10_rent_price: number | null;
  p90_rent_price: number | null;
  min_rent_price: number;
  max_rent_price: number;
};

/** Groupe de prix de `GET /api/v1/market/prices` au grain quartier × type × chambres. */
export type PriceGroup = {
  city: string;
  neighborhood: string | null;
  neighborhood_recognized: boolean | null;
  property_type: string | null;
  bedrooms: number | null;
  stats: MarketStats;
};

/** Réponse de `GET /api/v1/market/prices` (ticket #53). */
export type PricesResponse = {
  currency: "XAF";
  min_publish_n: number;
  n_observations: number;
  groups: PriceGroup[];
};

/** Quartier de `GET /api/v1/market/neighborhoods` (ticket #53). */
export type NeighborhoodMarket = {
  neighborhood: string;
  neighborhood_recognized: boolean;
  stats: {
    n_observations: number;
    mean_rent_price: number;
    min_rent_price: number;
    max_rent_price: number;
  };
};

/** Réponse de `GET /api/v1/market/neighborhoods`, restreinte aux champs lus. */
export type NeighborhoodsResponse = {
  currency: "XAF";
  min_publish_n: number;
  city: string;
  n_observations: number;
  n_neighborhoods: number;
  neighborhoods: NeighborhoodMarket[];
};
