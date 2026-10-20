/**
 * Formatage des montants (`context/ui-context.md` §Formats de réponse).
 *
 * Le séparateur de milliers vient de `Intl.NumberFormat("fr-FR")` — jamais
 * d'une image mentale inventée ; l'unité `FCFA / mois` est posée par l'écran.
 */

const amoutFormatter = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });

/** Montant en FCFA, milliers séparés ; `null`/`undefined` → chaîne explicite. */
export function formatFcfa(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) {
    return "Non publiée";
  }
  return `${amoutFormatter.format(amount)} FCFA`;
}

/** Fourchette textuelle `« 165 000 – 205 000 FCFA »`, bornes croisées signalées. */
export function formatRange(lower: number, upper: number): string {
  if (lower > upper) {
    return "Fourchette invalide (borne basse au-dessus de la borne haute)";
  }
  return `${amoutFormatter.format(lower)} – ${amoutFormatter.format(upper)} FCFA`;
}
