import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  API_BASE_URL_ENV,
  ApiError,
  DEFAULT_TIMEOUT_MS,
  apiBaseUrl,
  apiGet,
  apiPost,
} from "./api";

const BASE_URL = "http://127.0.0.1:8000";

function mockFetch(implementation: typeof fetch) {
  const fetchMock = vi.fn(implementation);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = BASE_URL;
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  delete process.env.NEXT_PUBLIC_API_BASE_URL;
});

describe("configuration", () => {
  it("refuse une base absente en nommant la variable", () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;

    expect(() => apiBaseUrl()).toThrowError(ApiError);
    try {
      apiBaseUrl();
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).kind).toBe("config");
      expect((error as ApiError).message).toContain(API_BASE_URL_ENV);
    }
  });

  it("refuse une base qui n'est pas une URL", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "pas-une-url";

    expect(() => apiBaseUrl()).toThrowError(/URL valide/);
  });

  it("refuse un protocole non http(s)", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "ftp://api.test";

    expect(() => apiBaseUrl()).toThrowError(/http\(s\)/);
  });

  it("normalise la barre oblique finale", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = `${BASE_URL}/`;

    expect(apiBaseUrl()).toBe(BASE_URL);
  });
});

describe("requêtes", () => {
  it("construit l'URL de l'API et demande du JSON", async () => {
    const fetchMock = mockFetch(async () => new Response(JSON.stringify({ ok: true })));

    const payload = await apiGet<{ ok: boolean }>("/api/v1/health");

    expect(payload).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE_URL}/api/v1/health`);
    expect(init.method).toBe("GET");
    expect(new Headers(init.headers).get("Accept")).toBe("application/json");
  });

  it("envoie un corps JSON en POST avec son type", async () => {
    const fetchMock = mockFetch(async () => new Response(JSON.stringify({ ok: true })));

    await apiPost("/api/v1/predictions", { city: "Douala" });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.body).toBe(JSON.stringify({ city: "Douala" }));
    expect(new Headers(init.headers).get("Content-Type")).toBe("application/json");
  });
});

describe("échecs", () => {
  it("classe un échec réseau sans exposer l'erreur d'origine", async () => {
    mockFetch(async () => {
      throw new TypeError("fetch failed: ECONNREFUSED");
    });

    await expect(apiGet("/api/v1/health")).rejects.toMatchObject({
      kind: "network",
      message: "L'API est momentanément injoignable.",
    });
  });

  it("signale un délai dépassé", async () => {
    vi.useFakeTimers();
    mockFetch(
      (_input, init) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("Aborted", "AbortError"));
          });
        }),
    );

    const pending = apiGet("/api/v1/health");
    const assertion = expect(pending).rejects.toMatchObject({ kind: "timeout" });
    await vi.advanceTimersByTimeAsync(DEFAULT_TIMEOUT_MS + 1);
    await assertion;
  });

  it("reprend le code et le détail de l'enveloppe d'erreur de l'API", async () => {
    mockFetch(
      async () =>
        new Response(
          JSON.stringify({
            error: {
              code: "validation_error",
              message: "Entrée invalide.",
              details: [{ field: "area_m2", message: "Extra inputs are not permitted" }],
            },
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        ),
    );

    const error = (await apiGet("/api/v1/predictions").catch((caught) => caught)) as ApiError;

    expect(error).toBeInstanceOf(ApiError);
    expect(error.kind).toBe("http");
    expect(error.status).toBe(422);
    expect(error.code).toBe("validation_error");
    expect(error.message).toBe("Entrée invalide.");
    expect(error.details).toEqual([
      { field: "area_m2", message: "Extra inputs are not permitted" },
    ]);
  });

  it("ne recopie pas une erreur serveur non JSON", async () => {
    mockFetch(async () => new Response("<html>Erreur</html>", { status: 500 }));

    const error = (await apiGet("/api/v1/health").catch((caught) => caught)) as ApiError;

    expect(error.kind).toBe("http");
    expect(error.status).toBe(500);
    expect(error.message).toBe("L'API a répondu 500.");
    expect(error.message).not.toContain("<html>");
  });

  it("signale une réponse 200 illisible", async () => {
    mockFetch(async () => new Response("pas du json", { status: 200 }));

    await expect(apiGet("/api/v1/health")).rejects.toMatchObject({
      kind: "invalid",
      status: 200,
    });
  });
});
