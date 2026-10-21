/**
 * Vocabulaire du domaine côté interface (source unique des listes de choix).
 *
 * Aligné sur `backend/domain/vocabulary.py` : une valeur absente des données ne
 * doit jamais être proposée, sous peine de fabriquer une requête que l'API
 * refusera (ou, pire, une statistique sans observation). Les libellés français
 * sont posés ici une seule fois, pour que les écrans d'estimation et
 * d'exploration ne divergent pas.
 */

export const CITIES = ["Douala", "Yaoundé"] as const;

export const PROPERTY_TYPES = [
  { value: "apartment", label: "Appartement" },
  { value: "studio", label: "Studio" },
  { value: "room", label: "Chambre (room)" },
  { value: "house", label: "Maison" },
] as const;

/** Bornes de pièces, identiques à la plateforme data et aux schémas de l'API. */
export const ROOMS_MIN = 0;
export const ROOMS_MAX = 10;

const PROPERTY_TYPE_LABELS = new Map<string, string>(
  PROPERTY_TYPES.map((type) => [type.value, type.label]),
);

/** Libellé français d'un type de bien ; la valeur brute si elle est inconnue. */
export function propertyTypeLabel(value: string | null | undefined): string {
  if (value === null || value === undefined) {
    return "Tous types";
  }
  return PROPERTY_TYPE_LABELS.get(value) ?? value;
}

/** Nombre de chambres lisible ; `null` signifie « filtre non appliqué ». */
export function bedroomsLabel(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "Toutes";
  }
  return value === 1 ? "1 chambre" : `${value} chambres`;
}

/** Choix de chambres proposés par les filtres (bornes de la plateforme data). */
export function roomChoices(): number[] {
  return Array.from({ length: ROOMS_MAX - ROOMS_MIN + 1 }, (_, index) => ROOMS_MIN + index);
}
