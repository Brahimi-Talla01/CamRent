import { describe, expect, it } from "vitest";

import type {
  NeighborhoodMarket,
  NeighborhoodsResponse,
  PriceGroup,
  PricesResponse,
} from "./api-types";
import {
  findMarketGroup,
  marketPricesUrl,
  neighborhoodsUrl,
  neighborhoodOptions,
} from "./market";

const QUALITY = {
  n_price_bound: 0,
  pct_price_bound: 0,
  n_republication: 0,
  pct_republication: 0,
  n_neighborhood_unrecognized: null,
  pct_neighborhood_unrecognized: null,
} as const;

function neighborhoodsResponse(
  names: string[],
): NeighborhoodsResponse {
  const items: NeighborhoodMarket[] = names.map((name) => ({
    neighborhood: name,
    neighborhood_recognized: true,
    n_groups: 1,
    stats: {
      n_observations: 10,
      mean_rent_price: 100_000,
      min_rent_price: 50_000,
      max_rent_price: 200_000,
    },
    quality: QUALITY,
  }));
  return {
    currency: "XAF",
    min_publish_n: 30,
    observed_period: { start: "2026-10-01", end: "2026-10-09" },
    city: "Douala",
    n_observations: items.length * 10,
    n_neighborhoods: items.length,
    neighborhoods: items,
  };
}

describe("neighborhoodOptions", () => {
  it("dédoublonne, trie et propose les libellés réels", () => {
    const response = neighborhoodsResponse(["Bonapriso", "Akwa", "Bonapriso", "Cité des Palmiers"]);

    expect(neighborhoodOptions(response)).toEqual([
      "Akwa",
      "Bonapriso",
      "Cité des Palmiers",
    ]);
  });

  it("rend une liste vide explicite sans quartier", () => {
    expect(neighborhoodOptions(neighborhoodsResponse([]))).toEqual([]);
  });
});

describe("urls", () => {
  it("encode la ville et le quartier (accents, espaces)", () => {
    expect(neighborhoodsUrl("Yaoundé")).toBe(
      "/api/v1/market/neighborhoods?city=Yaound%C3%A9",
    );
    expect(
      marketPricesUrl({
        city: "Douala",
        neighborhood: "Cité des Palmiers",
        property_type: "apartment",
        bedrooms: 2,
      }),
    ).toBe(
      "/api/v1/market/prices?city=Douala&neighborhood=" +
        "Cit%C3%A9%20des%20Palmiers&property_type=apartment&bedrooms=2",
    );
  });
});

describe("findMarketGroup", () => {
  const pricesResponse = (groups: PriceGroup[]): PricesResponse => ({
    currency: "XAF",
    min_publish_n: 30,
    observed_period: { start: "2026-10-01", end: "2026-10-09" },
    n_observations: groups.reduce((total, group) => total + group.stats.n_observations, 0),
    groups,
  });

  function group(overrides: Partial<PriceGroup> = {}): PriceGroup {
    return {
      city: "Douala",
      neighborhood: "Bonamoussadi",
      neighborhood_recognized: true,
      property_type: "apartment",
      bedrooms: 2,
      stats: {
        n_observations: 632,
        mean_rent_price: 98_498,
        median_rent_price: 90_000,
        median_published: true,
        p10_rent_price: 60_000,
        p90_rent_price: 150_000,
        min_rent_price: 40_000,
        max_rent_price: 400_000,
      },
      quality: QUALITY,
      ...overrides,
    };
  }

  it("retrouve le groupe exact au grain type × chambres", () => {
    const response = pricesResponse([group({ bedrooms: 3 }), group(), group({ property_type: "studio" })]);

    expect(findMarketGroup(response, { property_type: "apartment", bedrooms: 2 })).toBe(
      response.groups[1],
    );
  });

  it("rend null quand aucun groupe ne correspond (jamais de statistique inventée)", () => {
    const response = pricesResponse([group({ bedrooms: 3 })]);

    expect(
      findMarketGroup(response, { property_type: "apartment", bedrooms: 5 }),
    ).toBeNull();
  });
});
