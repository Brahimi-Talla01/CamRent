import { describe, expect, it } from "vitest";

import { ApiError } from "./api";
import { estimationFailureMessage, fieldErrorsFromDetails } from "./estimation-errors";

describe("estimationFailureMessage", () => {
  it("explique le refus d'un quartier jamais observé (404)", () => {
    const error = new ApiError("http", "Quartier inconnu du modèle.", {
      status: 404,
      code: "not_found",
    });

    const message = estimationFailureMessage(error);

    expect(message).toContain("Quartier inconnu du modèle.");
    expect(message).toContain("jamais observé");
    expect(message).toContain("quartier de la liste");
  });

  it("reprend le message stable du client d'API pour les autres échecs", () => {
    const network = new ApiError("network", "L'API est momentanément injoignable.");
    expect(estimationFailureMessage(network)).toBe("L'API est momentanément injoignable.");

    const server = new ApiError("http", "L'API a répondu 500.", { status: 500 });
    expect(estimationFailureMessage(server)).toBe("L'API a répondu 500.");
  });

  it("ne fuite jamais l'exception d'origine (AGENTS.md §9)", () => {
    expect(estimationFailureMessage(new TypeError("fetch failed: ECONNREFUSED"))).not.toContain(
      "ECONNREFUSED",
    );
  });
});

describe("fieldErrorsFromDetails", () => {
  it("porte le détail sur le champ concerné", () => {
    const errors = fieldErrorsFromDetails([
      { field: "bedrooms", message: "Input should be a valid integer" },
    ]);

    expect(errors.bedrooms).toBe("Input should be a valid integer");
    expect(errors.form).toBeUndefined();
  });

  it("garde à côté du formulaire les erreurs des champs non observables", () => {
    const errors = fieldErrorsFromDetails([
      { field: "city", message: "Input should be 'Douala' or 'Yaoundé'" },
      { field: "bathrooms", message: "greater than or equal to 0" },
    ]);

    expect(errors.bathrooms).toBe("greater than or equal to 0");
    expect(errors.form).toContain("city");
  });

  it("ne garde qu'une seule erreur par champ (première reçue)", () => {
    const errors = fieldErrorsFromDetails([
      { field: "neighborhood", message: "première" },
      { field: "neighborhood", message: "deuxième" },
    ]);

    expect(errors.neighborhood).toBe("première");
  });
});
