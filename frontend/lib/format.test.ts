import { describe, expect, it } from "vitest";

import { formatCount, formatDate, formatFcfa, formatRange, formatShare } from "./format";

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

describe("formatCount", () => {
  it("sépare les milliers sans unité inventée", () => {
    expect(formatCount(2811)).toMatch(/^2[\u00a0\u202f]811$/);
  });
});

describe("formatShare", () => {
  it("affiche une part à une décimale au plus, avec l'espace avant %", () => {
    expect(formatShare(3.02)).toBe("3\u00a0%");
    expect(formatShare(12.46)).toBe("12,5\u00a0%");
  });
});

describe("formatDate", () => {
  it("rend une date ISO en clair, sans décalage de fuseau", () => {
    expect(formatDate("2026-10-01")).toBe("1 octobre 2026");
  });

  it("signale une date absente ou invalide", () => {
    expect(formatDate(null)).toBe("date inconnue");
    expect(formatDate("pas-une-date")).toBe("date inconnue");
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
