/**
 * Helpers purs de l'écran d'exploration du marché (09a.3).
 *
 * Trois responsabilités, toutes testables hors DOM :
 *
 * - **Lire les filtres depuis l'URL** et n'accepter que des valeurs que l'API
 *   connaît. Un paramètre forgé (`bedrooms=99`, type inconnu) est ignoré, jamais
 *   relayé : l'écran ne fabrique pas de requête invalide.
 * - **Construire les URLs** des endpoints de marché, avec les mêmes noms de
 *   paramètres que l'API et un encodage sans ambiguïté (`%20`, pas `+`).
 * - **Décider ce qui peut être affiché** : une médiane n'est montrée que si elle
 *   est réellement publiée *et* au-dessus du seuil, même si une réponse
 *   incohérente la proposait (défense en profondeur, comme côté API).
 *
 * Aucune statistique n'est calculée ici : les marts restent la seule source
 * (spec 08 §3), l'écran ne fait que lire et présenter.
 */

import type { MarketQuality, MarketStats } from "./api-types";
import {
  CITIES,
  PROPERTY_TYPES,
  ROOMS_MAX,
  ROOMS_MIN,
  bedroomsLabel,
  propertyTypeLabel,
} from "./vocabulary";

export type ExplorerFilters = {
  city: string;
  neighborhood: string | null;
  propertyType: string | null;
  bedrooms: number | null;
};

/** Sous-ensemble de `URLSearchParams` suffisant pour lire des filtres. */
export type FiltersSource = { get(name: string): string | null };

const PROPERTY_TYPE_VALUES = new Set<string>(
  PROPERTY_TYPES.map((type) => type.value),
);

/** Même borne que le schéma de l'API (`NEIGHBORHOOD_MAX_LENGTH`). */
const NEIGHBORHOOD_MAX_LENGTH = 120;

/**
 * Filtres valides lus dans l'URL, avec des valeurs par défaut sûres.
 *
 * Ville inconnue → première ville du vocabulaire ; type inconnu, chambres hors
 * bornes ou quartier démesuré → filtre non appliqué. Une URL partagée ne peut
 * donc pas produire une requête hors contrat.
 */
export function parseExplorerFilters(params: FiltersSource): ExplorerFilters {
  const requestedCity = (params.get("city") ?? "").trim();
  const city = (CITIES as readonly string[]).includes(requestedCity)
    ? requestedCity
    : CITIES[0];

  const requestedNeighborhood = (params.get("neighborhood") ?? "").trim();
  const neighborhood =
    requestedNeighborhood.length > 0 &&
    requestedNeighborhood.length <= NEIGHBORHOOD_MAX_LENGTH
      ? requestedNeighborhood
      : null;

  const requestedType = (params.get("property_type") ?? "").trim();
  const propertyType = PROPERTY_TYPE_VALUES.has(requestedType)
    ? requestedType
    : null;

  const requestedBedrooms = (params.get("bedrooms") ?? "").trim();
  const bedroomCount = Number(requestedBedrooms);
  const bedrooms =
    requestedBedrooms !== "" &&
    Number.isInteger(bedroomCount) &&
    bedroomCount >= ROOMS_MIN &&
    bedroomCount <= ROOMS_MAX
      ? bedroomCount
      : null;

  return { city, neighborhood, propertyType, bedrooms };
}

function filterQuery(
  filters: ExplorerFilters,
  { withNeighborhood }: { withNeighborhood: boolean },
): string {
  // `encodeURIComponent` plutôt que `URLSearchParams` : celui-ci encode les
  // espaces en `+`, ambigu selon le serveur ; `%20` ne l'est jamais.
  const parts = [`city=${encodeURIComponent(filters.city)}`];
  if (withNeighborhood && filters.neighborhood !== null) {
    parts.push(`neighborhood=${encodeURIComponent(filters.neighborhood)}`);
  }
  if (filters.propertyType !== null) {
    parts.push(`property_type=${encodeURIComponent(filters.propertyType)}`);
  }
  if (filters.bedrooms !== null) {
    parts.push(`bedrooms=${encodeURIComponent(String(filters.bedrooms))}`);
  }
  return parts.join("&");
}

/** Lecture agrégée par quartier (N, moyenne, min–max), filtrable par type et chambres. */
export function neighborhoodsPath(filters: ExplorerFilters): string {
  return `/api/v1/market/neighborhoods?${filterQuery(filters, { withNeighborhood: false })}`;
}

/**
 * Détail au grain (quartier × type × chambres), avec médiane et centiles.
 * `null` tant qu'aucun quartier n'est choisi : `/market/prices` exige `city`
 * avec `neighborhood`, et une statistique de ville ne remplacerait pas un
 * détail de quartier.
 */
export function pricesPath(filters: ExplorerFilters): string | null {
  if (filters.neighborhood === null) {
    return null;
  }
  return `/api/v1/market/prices?${filterQuery(filters, { withNeighborhood: true })}`;
}

/** URL partageable de l'écran, sans paramètre vide (ville toujours présente). */
export function explorerHref(filters: ExplorerFilters): string {
  return `/explorer?${filterQuery(filters, { withNeighborhood: true })}`;
}

export type MedianDisplay =
  | { published: true; amount: number }
  | { published: false; belowThreshold: boolean };

/**
 * Ce que l'écran a le droit d'afficher comme médiane.
 *
 * Le seuil est revérifié côté écran : une réponse qui publierait une médiane
 * sous 30 observations pour cause de régression amont ne doit pas la rendre
 * visible ici (l'invariant produit prime sur un champ reçu).
 */
export function medianDisplay(
  stats: Pick<
    MarketStats,
    "n_observations" | "median_rent_price" | "median_published"
  >,
  minPublishN: number,
): MedianDisplay {
  const belowThreshold = stats.n_observations < minPublishN;
  if (
    belowThreshold ||
    !stats.median_published ||
    stats.median_rent_price === null
  ) {
    return { published: false, belowThreshold };
  }
  return { published: true, amount: stats.median_rent_price };
}

export type QualityNote = {
  key: "price_bound" | "republication" | "neighborhood_unrecognized";
  label: string;
  count: number;
  percent: number;
};

/**
 * Biais réellement présents, avec leur volume et leur part.
 *
 * Les valeurs nulles sont omises : signaler « 0 prix borné » noierait les
 * limites qui comptent. Chaque ligne porte son nombre d'observations.
 */
export function qualityNotes(quality: MarketQuality): QualityNote[] {
  const notes: QualityNote[] = [];
  if (quality.n_price_bound > 0) {
    notes.push({
      key: "price_bound",
      label: "Prix « à partir de » (borne basse, pas un prix complet)",
      count: quality.n_price_bound,
      percent: quality.pct_price_bound,
    });
  }
  if (quality.n_republication > 0) {
    notes.push({
      key: "republication",
      label: "Annonces republiées",
      count: quality.n_republication,
      percent: quality.pct_republication,
    });
  }
  if ((quality.n_neighborhood_unrecognized ?? 0) > 0) {
    notes.push({
      key: "neighborhood_unrecognized",
      label: "Observations sur un quartier non reconnu",
      count: quality.n_neighborhood_unrecognized ?? 0,
      percent: quality.pct_neighborhood_unrecognized ?? 0,
    });
  }
  return notes;
}

/** Phrase de l'état vide : les filtres appliqués, aucun chiffre. */
export function emptyStateMessage(filters: ExplorerFilters): string {
  const scope = [
    filters.city,
    filters.neighborhood ?? "tous les quartiers",
    filters.propertyType === null
      ? "tous les types"
      : propertyTypeLabel(filters.propertyType),
    filters.bedrooms === null ? "toutes chambres" : bedroomsLabel(filters.bedrooms),
  ];
  return `Aucune observation collectée pour ${scope.join(" · ")}.`;
}

/** Le filtre de quartier (ou tous les filtres) est-il actif ? */
export function hasActiveFilters(filters: ExplorerFilters): boolean {
  return (
    filters.neighborhood !== null ||
    filters.propertyType !== null ||
    filters.bedrooms !== null
  );
}
