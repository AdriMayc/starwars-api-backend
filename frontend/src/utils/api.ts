// frontend/src/utils/api.ts
import type { ApiEnvelope, ResourceType, Resource, RelatedItem } from "../types/api";

type ErrorLike = { code?: string; message?: string };

type CacheEntry = { ts: number; value: ApiEnvelope<any> };

const DEFAULT_TTL_MS = 60_000; // 60s (ajuste se quiser)
const cache = new Map<string, CacheEntry>();
const inFlight = new Map<string, Promise<ApiEnvelope<any>>>();

function buildQuery(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    const s = String(v).trim();
    if (!s) continue;
    sp.set(k, s);
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : "";
}

function normalizeErrors(errors: unknown): string[] {
  if (!errors) return [];
  if (Array.isArray(errors)) {
    return errors.map((e: unknown) => {
      if (typeof e === "string") return e;
      const obj = e as ErrorLike;
      if (obj?.message) return String(obj.message);
      if (obj?.code) return String(obj.code);
      return "Unknown error";
    });
  }
  return ["Unknown error"];
}

// --- abort helper (por consumidor) ---
function abortError(): any {
  // DOMException existe no browser; fallback para ambientes de teste
  try {
    return new DOMException("Aborted", "AbortError");
  } catch {
    const err: any = new Error("Aborted");
    err.name = "AbortError";
    return err;
  }
}

function withAbort<T>(p: Promise<T>, signal?: AbortSignal): Promise<T> {
  if (!signal) return p;
  if (signal.aborted) return Promise.reject(abortError());

  return Promise.race([
    p,
    new Promise<T>((_, reject) => {
      signal.addEventListener("abort", () => reject(abortError()), { once: true });
    }),
  ]);
}

async function requestEnvelope<T>(path: string): Promise<ApiEnvelope<T>> {
  const apiKey = import.meta.env.VITE_API_KEY as string | undefined;

  const headers: Record<string, string> = { accept: "application/json" };
  if (apiKey) headers["x-api-key"] = apiKey;

  const res = await fetch(path, { headers });
  const text = await res.text();

  let json: any;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    return {
      data: [] as any,
      meta: { request_id: "n/a" },
      links: { self: path, next: null, prev: null },
      errors: ["Invalid JSON response"],
    };
  }

  if (json && typeof json === "object" && "errors" in json) {
    json.errors = normalizeErrors(json.errors);
  }

  if (!res.ok) {
    const reqId = json?.meta?.request_id ?? "n/a";
    const errs = normalizeErrors(json?.errors) || [];
    const msg = json?.message ? [String(json.message)] : [];
    return {
      data: [] as any,
      meta: { request_id: reqId },
      links: { self: path, next: null, prev: null },
      errors: errs.length ? errs : msg.length ? msg : [`HTTP ${res.status}`],
    };
  }

  return json as ApiEnvelope<T>;
}

// --- cache/dedupe wrapper ---
function cacheKey(path: string): string {
  // inclui apiKey porque muda identidade do request
  const apiKey = import.meta.env.VITE_API_KEY as string | undefined;
  return `${apiKey ?? "no-key"}|${path}`;
}

export function peekCachedEnvelope<T>(path: string): ApiEnvelope<T> | null {
  const key = cacheKey(path);
  const entry = cache.get(key);
  if (!entry) return null;
  const age = Date.now() - entry.ts;
  if (age > DEFAULT_TTL_MS) return null;
  return entry.value as ApiEnvelope<T>;
}

async function requestEnvelopeCached<T>(path: string, signal?: AbortSignal): Promise<ApiEnvelope<T>> {
  const key = cacheKey(path);

  const cached = cache.get(key);
  if (cached && Date.now() - cached.ts <= DEFAULT_TTL_MS) {
    return cached.value as ApiEnvelope<T>;
  }

  const inflight = inFlight.get(key);
  if (inflight) {
    return withAbort(inflight as Promise<ApiEnvelope<T>>, signal) as Promise<ApiEnvelope<T>>;
  }

  const p = requestEnvelope<T>(path)
    .then((env) => {
      cache.set(key, { ts: Date.now(), value: env });
      return env;
    })
    .finally(() => {
      inFlight.delete(key);
    });

  inFlight.set(key, p as Promise<ApiEnvelope<any>>);
  return withAbort(p, signal);
}

// builders (para reutilizar no App e pegar cache)
export function buildResourcesPath(resource: ResourceType, page: number, pageSize: number, q: string) {
  const query = buildQuery({
    page,
    page_size: pageSize,
    q: q?.trim() ? q.trim() : undefined,
  });
  return `/api/${resource}${query}`;
}

export function buildRelatedPath(
  resource: "films" | "planets",
  id: number,
  rel: "characters" | "residents",
  page: number = 1,
  pageSize: number = 10,
  q?: string
) {
  const query = buildQuery({
    page,
    page_size: pageSize,
    q: q?.trim() ? q.trim() : undefined,
  });
  return `/api/${resource}/${id}/${rel}${query}`;
}

// LIST
export async function fetchResources(
  resource: ResourceType,
  page: number,
  pageSize: number,
  q: string,
  signal?: AbortSignal
): Promise<ApiEnvelope<Resource>> {
  const path = buildResourcesPath(resource, page, pageSize, q);
  return requestEnvelopeCached<Resource>(path, signal);
}

// RELATED
export async function fetchRelated(
  resource: "films" | "planets",
  id: number,
  rel: "characters" | "residents",
  signal?: AbortSignal,
  page: number = 1,
  pageSize: number = 10,
  q?: string
): Promise<ApiEnvelope<RelatedItem>> {
  const path = buildRelatedPath(resource, id, rel, page, pageSize, q);
  return requestEnvelopeCached<RelatedItem>(path, signal);
}
