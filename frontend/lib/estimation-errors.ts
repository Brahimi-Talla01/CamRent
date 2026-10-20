/**
 * Traduction des échecs d'estimation en messages d'écran (09a.2).
 *
 * Pur, testé hors DOM : une `ApiError` devient une phrase du produit : 404
 * « quartier jamais observé », 422 portée champ par champ depuis le détail de
 * l'enveloppe d'erreur, le reste recopie le message stable du client d'API.
 */

import { ApiError, type ApiErrorDetail } from "./api";

export type FieldErrors = Partial<Record<"neighborhood" | "bedrooms" | "bathrooms" | "form", string>>;

/** Traduit l'échec de l'API vers un message d'écran, sans jargon technique. */
export function estimationFailureMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return "L'estimation n'a pas pu être effectuée. Réessayez.";
  }
  if (error.status === 404) {
    return (
      `${error.message} Le modèle n'estime pas un quartier qu'il n'a jamais ` +
      "observé avec cette ville : vérifiez l'orthographe ou choisissez un " +
      "quartier de la liste."
    );
  }
  return error.message;
}

/** Répartit un 422 sur les champs du formulaire (détail de l'enveloppe d'erreur). */
export function fieldErrorsFromDetails(details: ApiErrorDetail[]): FieldErrors {
  const errors: FieldErrors = {};
  for (const detail of details) {
    if (detail.field === "neighborhood" || detail.field === "bedrooms" || detail.field === "bathrooms") {
      errors[detail.field] ??= detail.message;
    } else {
      // Les autres champs sont fixes (liste de choix) : l'erreur de cohérence
      // reste à côté du formulaire plutôt que sur un champ non observable.
      errors.form ??= `${detail.field} : ${detail.message}`;
    }
  }
  return errors;
}
