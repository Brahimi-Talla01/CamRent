import { describe, expect, it } from "vitest";

import type { MarketQuality, MarketStats } from "./api-types";
import {
  emptyStateMessage,
  explorerHref,
  hasActiveFilters,
  medianDisplay,
  neighborhoodsPath,
  parseExplorerFilters,
  pricesPath,
  qualityNotes,
} from "./explorer";

function filtersFrom(query: string) {
  return parseExplorerFilters(new URLSearchParams(query));
}

function stats(overrides: Partial<MarketStats> = {}): MarketStats {
  return {
    n_observations: 632,
    mean_rent_price: 98_498,
    median_rent_price: 90_000,
    median_published: true,
    p10_rent_price: 70_000,
    p90_rent_price: 150_000,
    min_rent_price: 40_000,
    max_rent_price: 400_000,
    ...overrides,
  };
}

function quality(overrides: Partial<MarketQuality> = {}): MarketQuality {
  return {
    n_price_bound: 0,
    pct_price_bound: 0,
    n_republication: 0,
    pct_republication: 0,
    n_neighborhood_unrecognized: null,
    pct_neighborhood_unrecognized: null,
    ...overrides,
  };
}

describe("parseExplorerFilters", () => {
  it("part de Douala, sans filtre de détail, quand l'URL est vide", () => {
    expect(filtersFrom("")).toEqual({
      city: "Douala",
      neighborhood: null,
      propertyType: null,
      bedrooms: null,
    });
  });

  it("lit des filtres valides, accents et espaces compris", () => {
    expect(
      filtersFrom(
        "city=Yaound%C3%A9&neighborhood=Cit%C3%A9%20des%20Palmiers&property_type=studio&bedrooms=2",
      ),
    ).toEqual({
      city: "Yaoundé",
      neighborhood: "Cité des Palmiers",
      propertyType: "studio",
      bedrooms: 2,
    });
  });

  it("ignore une ville, un type ou un nombre de chambres hors contrat", () => {
    // Une URL forgée ne doit jamais produire une requête que l'API refusera.
    expect(filtersFrom("city=Conakry&property_type=villa&bedrooms=11")).toEqual({
      city: "Douala",
      neighborhood: null,
      propertyType: null,
      bedrooms: null,
    });
    expect(filtersFrom("bedrooms=-1").bedrooms).toBeNull();
    expect(filtersFrom("bedrooms=1.5").bedrooms).toBeNull();
    expect(filtersFrom("bedrooms=abc").bedrooms).toBeNull();
  });

  it("refuse un quartier démesuré ou vide", () => {
    expect(filtersFrom(`neighborhood=${"a".repeat(121)}`).neighborhood).toBeNull();
    expect(filtersFrom("neighborhood=%20%20").neighborhood).toBeNull();
  });
});

describe("URLs de l'API", () => {
  it("demande la synthèse par quartier sans jamais y ajouter le quartier", () => {
    expect(
      neighborhoodsPath({
        city: "Douala",
        neighborhood: "Bonapriso",
        propertyType: "apartment",
        bedrooms: 1,
      }),
    ).toBe(
      "/api/v1/market/neighborhoods?city=Douala&property_type=apartment&bedrooms=1",
    );
  });

  it("encode les espaces en %20 et les accents", () => {
    expect(
      neighborhoodsPath({
        city: "Yaoundé",
        neighborhood: null,
        propertyType: null,
        bedrooms: null,
      }),
    ).toBe("/api/v1/market/neighborhoods?city=Yaound%C3%A9");
  });

  it("n'appelle pas le détail sans quartier choisi", () => {
    expect(
      pricesPath({
        city: "Douala",
        neighborhood: null,
        propertyType: "apartment",
        bedrooms: 2,
      }),
    ).toBeNull();

    expect(
      pricesPath({
        city: "Douala",
        neighborhood: "Cité des Palmiers",
        propertyType: "apartment",
        bedrooms: 1,
      }),
    ).toBe(
      "/api/v1/market/prices?city=Douala&neighborhood=Cit%C3%A9%20des%20Palmiers" +
        "&property_type=apartment&bedrooms=1",
    );
  });

  it("construit une URL partageable sans paramètre vide", () => {
    expect(
      explorerHref({
        city: "Douala",
        neighborhood: null,
        propertyType: null,
        bedrooms: null,
      }),
    ).toBe("/explorer?city=Douala");
  });
});

describe("medianDisplay", () => {
  it("publie la médiane au-dessus du seuil", () => {
    expect(medianDisplay(stats(), 30)).toEqual({ published: true, amount: 90_000 });
  });

  it("ne publie jamais une médiane sous le seuil, même si la réponse la propose", () => {
    // Défense en profondeur : l'invariant produit prime sur un champ reçu.
    const inconsistent = stats({
      n_observations: 25,
      median_rent_price: 269_000,
      median_published: true,
    });

    expect(medianDisplay(inconsistent, 30)).toEqual({
      published: false,
      belowThreshold: true,
    });
  });

  it("respecte un flag de non-publication au-dessus du seuil", () => {
    const withheld = stats({ median_published: false });

    expect(medianDisplay(withheld, 30)).toEqual({
      published: false,
      belowThreshold: false,
    });
  });

  it("traite une médiane nulle comme non publiée", () => {
    expect(
      medianDisplay(stats({ median_rent_price: null, median_published: false }), 30),
    ).toEqual({ published: false, belowThreshold: false });
  });
});

describe("qualityNotes", () => {
  it("n'annonce aucun biais quand aucun n'est constaté", () => {
    expect(qualityNotes(quality())).toEqual([]);
  });

  it("signale chaque biais présent avec son volume et sa part", () => {
    const notes = qualityNotes(
      quality({
        n_price_bound: 85,
        pct_price_bound: 3.02,
        n_republication: 42,
        pct_republication: 1.49,
        n_neighborhood_unrecognized: 12,
        pct_neighborhood_unrecognized: 0.43,
      }),
    );

    expect(notes.map((note) => note.key)).toEqual([
      "price_bound",
      "republication",
      "neighborhood_unrecognized",
    ]);
    expect(notes[0]).toMatchObject({ count: 85, percent: 3.02 });
    expect(notes[1]).toMatchObject({ count: 42, percent: 1.49 });
    expect(notes[2]).toMatchObject({ count: 12, percent: 0.43 });
  });

  it("n'invente pas un biais de quartier au niveau quartier (champ nul)", () => {
    const notes = qualityNotes(
      quality({ n_price_bound: 3, pct_price_bound: 4.2 }),
    );

    expect(notes).toHaveLength(1);
    expect(notes[0]?.key).toBe("price_bound");
  });
});

describe("emptyStateMessage", () => {
  it("nomme les filtres appliqués sans produire de statistique", () => {
    const message = emptyStateMessage({
      city: "Yaoundé",
      neighborhood: "Bastos",
      propertyType: "apartment",
      bedrooms: 9,
    });

    expect(message).toBe(
      "Aucune observation collectée pour Yaoundé · Bastos · Appartement · 9 chambres.",
    );
    expect(message).not.toMatch(/FCFA/);
  });
});

describe("hasActiveFilters", () => {
  it("ne considère pas la ville seule comme un filtre à retirer", () => {
    expect(
      hasActiveFilters({
        city: "Yaoundé",
        neighborhood: null,
        propertyType: null,
        bedrooms: null,
      }),
    ).toBe(false);
    expect(
      hasActiveFilters({
        city: "Douala",
        neighborhood: null,
        propertyType: null,
        bedrooms: 2,
      }),
    ).toBe(true);
  });
});
