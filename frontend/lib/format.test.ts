import { describe, expect, it } from "vitest";

import { formatFcfa, formatRange } from "./format";

describe("formatFcfa", () => {
  it("met en FCFA avec séparateur de milliers insécable", () => {
    // U+00A0 (espace insécable) : Intl.NumberFormat("fr-FR") est la référence
    // imposée par `context/ui-context.md`, jamais un formatage manuel.
    expect(formatFcfa(185000)).toMatch(/^185[\u00a0\u202f]000 FCFA$/);
  });

  it("formate les petites valeurs sans séparateur", () => {
    expect(formatFcfa(1)).toBe("1 FCFA");
  });

  it("rend une chaîne explicite pour une valeur absente", () => {
    expect(formatFcfa(null)).toBe("Non publiée");
    expect(formatFcfa(undefined)).toBe("Non publiée");
  });
});

describe("formatRange", () => {
  it("formate la fourchette des deux bornes", () => {
    expect(formatRange(165000, 205000)).toMatch(/^165[\u00a0\u202f]000 – 205[\u00a0\u202f]000 FCFA$/);
  });

  it("affiche la même fourchette quand les bornes sont égales (reprise telle quelle du modèle)", () => {
    expect(formatRange(150000, 150000)).toMatch(/^150[\u00a0\u202f]000 – 150[\u00a0\u202f]000 FCFA$/);
  });

  it("signale des bornes croisées au lieu de les figer", () => {
    expect(formatRange(200000, 150000)).toContain("invalide");
  });
});
