/**
 * Helpers du marché pour l'écran d'estimation (09a.2).
 *
 * Modules purs, testés : construire les URLs de l'API publique, extraire les
 * options de quartier et retrouver le groupe de marché au grain du formulaire.
 * Aucune statistique n'est calculée ici : les marts restent la seule source
 * (spec 08 §3), l'écran ne fait que les lire.
 */

import type {
  NeighborhoodsResponse,
  PriceGroup,
  PricesResponse,
} from "./api-types";

/** Quartiers proposés en suggestion, libellés reconnus d'abord, triés. */
export function neighborhoodOptions(response: NeighborhoodsResponse): string[] {
  const named = response.neighborhoods.map((item) => item.neighborhood);
  return Array.from(new Set(named)).sort(
    (a, b) => a.localeCompare(b, "fr"),
  );
}

/**
 * URL de lecture des quartiers d'une ville.
 *
 * `encodeURIComponent` est indispensable : les libellés portent accents et
 * espaces (« Cité des Palmiers »).
 */
export function neighborhoodsUrl(city: string): string {
  return `/api/v1/market/neighborhoods?city=${encodeURIComponent(city)}`;
}

/** URL du groupe de marché au grain du formulaire (quartier impose `city`). */
export function marketPricesUrl(request: {
  city: string;
  neighborhood: string;
  property_type: string;
  bedrooms: number;
}): string {
  // `encodeURIComponent` plutôt que `URLSearchParams` : ce dernier encode les
  // espaces en `+`, ambigu selon le serveur ; `%20` ne l'est jamais.
  return (
    `/api/v1/market/prices?city=${encodeURIComponent(request.city)}` +
    `&neighborhood=${encodeURIComponent(request.neighborhood)}` +
    `&property_type=${encodeURIComponent(request.property_type)}` +
    `&bedrooms=${encodeURIComponent(String(request.bedrooms))}`
  );
}

/**
 * Groupe de prix correspondant au formulaire, au grain « quartier » des marts.
 *
 * Filtrer ici ne contrecarre jamais le backend : la réponse est déjà bornée par
 * les mêmes query params. Le groupe peut être absent (aucune observation de ce
 * type / de ce nombre de chambres dans le quartier) — l'écran le dira, sans
 * inventer de statistique.
 */
export function findMarketGroup(
  response: PricesResponse,
  request: { property_type: string; bedrooms: number },
): PriceGroup | null {
  return (
    response.groups.find(
      (group) =>
        group.property_type === request.property_type &&
        group.bedrooms === request.bedrooms &&
        group.neighborhood !== null,
    ) ?? null
  );
}
