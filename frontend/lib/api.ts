/**
 * Client de l'API publique CamRent (Phase 8a).
 *
 * Trois règles :
 *
 * - **Aucune URL en dur** : la base vient de `NEXT_PUBLIC_API_BASE_URL`
 *   (inlinée par Next au build). Variable absente ou invalide → `ApiError`
 *   `config`, message qui nomme la variable ;
 * - **Aucune erreur technique brute** : un échec réseau, un délai dépassé ou une
 *   réponse illisible deviennent une `ApiError` de type stable, sans exposer
 *   l'exception d'origine (AGENTS.md §9) ;
 * - **Une seule forme d'erreur HTTP** : l'enveloppe `{"error": {code, message,
 *   details}}` de l'API publique est conservée telle quelle, y compris le code
 *   et le détail par champ.
 */

export type ApiErrorKind = "config" | "network" | "timeout" | "http" | "invalid";

export type ApiErrorDetail = {
  field: string;
  message: string;
};

type ApiErrorOptions = {
  status?: number;
  code?: string;
  details?: ApiErrorDetail[];
};

/** Échec d'appel à l'API, classé pour que l'interface choisisse son message. */
export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly code?: string;
  readonly details: ApiErrorDetail[];

  constructor(kind: ApiErrorKind, message: string, options: ApiErrorOptions = {}) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = options.status;
    this.code = options.code;
    this.details = options.details ?? [];
  }
}

/** Nom de la variable d'environnement qui porte l'URL de l'API publique. */
export const API_BASE_URL_ENV = "NEXT_PUBLIC_API_BASE_URL";

/** Délai maximal d'un appel (l'interface ne doit pas rester bloquée). */
export const DEFAULT_TIMEOUT_MS = 8000;

/**
 * Base de l'API publique, normalisée sans barre oblique finale.
 *
 * @throws {ApiError} `config` si la variable manque, n'est pas une URL ou n'est
 *   pas en http(s).
 */
export function apiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (!raw) {
    throw new ApiError(
      "config",
      `L'URL de l'API publique n'est pas configurée (${API_BASE_URL_ENV}).`,
    );
  }

  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new ApiError("config", `${API_BASE_URL_ENV} n'est pas une URL valide.`);
  }

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new ApiError("config", `${API_BASE_URL_ENV} doit être une URL http(s).`);
  }

  return url.toString().replace(/\/$/, "");
}

function requestUrl(path: string): string {
  const base = apiBaseUrl();
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

function asErrorDetail(value: unknown): ApiErrorDetail | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const record = value as Record<string, unknown>;
  if (typeof record.field !== "string" || typeof record.message !== "string") {
    return null;
  }
  return { field: record.field, message: record.message };
}

function errorEnvelope(payload: unknown): {
  code?: string;
  message?: string;
  details: ApiErrorDetail[];
} | null {
  if (typeof payload !== "object" || payload === null) {
    return null;
  }
  const error = (payload as Record<string, unknown>).error;
  if (typeof error !== "object" || error === null) {
    return null;
  }
  const record = error as Record<string, unknown>;
  const details = Array.isArray(record.details)
    ? record.details.flatMap((item) => {
        const detail = asErrorDetail(item);
        return detail ? [detail] : [];
      })
    : [];
  return {
    code: typeof record.code === "string" ? record.code : undefined,
    message: typeof record.message === "string" ? record.message : undefined,
    details,
  };
}

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let payload: unknown;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = undefined;
    }
  }

  if (!response.ok) {
    const envelope = errorEnvelope(payload);
    throw new ApiError("http", envelope?.message ?? `L'API a répondu ${response.status}.`, {
      status: response.status,
      code: envelope?.code,
      details: envelope?.details,
    });
  }

  if (payload === undefined) {
    throw new ApiError("invalid", "La réponse de l'API est illisible (JSON attendu).", {
      status: response.status,
    });
  }

  return payload as T;
}

/**
 * Appelle l'API et renvoie le corps JSON typé.
 *
 * @throws {ApiError} `config`, `network`, `timeout`, `http` ou `invalid`.
 */
export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  const url = requestUrl(path);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const headers = new Headers(init.headers);
    if (!headers.has("Accept")) {
      headers.set("Accept", "application/json");
    }
    if (init.body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    let response: Response;
    try {
      response = await fetch(url, { ...init, headers, signal: controller.signal });
    } catch {
      if (controller.signal.aborted) {
        throw new ApiError("timeout", "L'API n'a pas répondu dans le délai imparti.");
      }
      throw new ApiError("network", "L'API est momentanément injoignable.");
    }

    return await parseResponse<T>(response);
  } finally {
    clearTimeout(timer);
  }
}

/** Lecture GET de l'API publique. */
export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path, { method: "GET", cache: "no-store" });
}

/** Écriture POST JSON vers l'API publique. */
export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, { method: "POST", body: JSON.stringify(body) });
}
