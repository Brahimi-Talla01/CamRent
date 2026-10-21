/**
 * Formatage des montants et des effectifs (`context/ui-context.md` §Formats de
 * réponse).
 *
 * Les séparateurs viennent de `Intl.NumberFormat("fr-FR")` — jamais d'une image
 * mentale inventée ; l'unité `FCFA / mois` est posée par l'écran.
 */

const amountFormatter = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
const shareFormatter = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 });
const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

/** Montant en FCFA, milliers séparés ; `null`/`undefined` → chaîne explicite. */
export function formatFcfa(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) {
    return "Non publiée";
  }
  return `${amountFormatter.format(amount)} FCFA`;
}

/** Fourchette textuelle `« 165 000 – 205 000 FCFA »`, bornes croisées signalées. */
export function formatRange(lower: number, upper: number): string {
  if (lower > upper) {
    return "Fourchette invalide (borne basse au-dessus de la borne haute)";
  }
  return `${amountFormatter.format(lower)} – ${amountFormatter.format(upper)} FCFA`;
}

/** Effectif lisible (`2 811`), sans unité inventée. */
export function formatCount(value: number): string {
  return amountFormatter.format(value);
}

/** Part en pourcentage (`12,4 %`), une décimale au plus. */
export function formatShare(percent: number): string {
  return `${shareFormatter.format(percent)}\u00a0%`;
}

/** Date ISO (`2026-10-01`) en clair ; `null` → absence explicite. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) {
    return "date inconnue";
  }
  const parsed = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) {
    return "date inconnue";
  }
  return dateFormatter.format(parsed);
}
