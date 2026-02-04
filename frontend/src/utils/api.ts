// frontend/src/utils/api.ts
import type { ApiEnvelope, ResourceType, Resource, RelatedItem } from "../types/api";

type ErrorLike = { code?: string; message?: string };

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
  // backend sempre manda array, mas mantém fallback
  return ["Unknown error"];
}

async function requestEnvelope<T>(
  path: string,
  signal?: AbortSignal
): Promise<ApiEnvelope<T>> {
  const apiKey = import.meta.env.VITE_API_KEY as string | undefined;

  const headers: Record<string, string> = { accept: "application/json" };
  if (apiKey) headers["x-api-key"] = apiKey;

  const res = await fetch(path, { headers, signal });
  const text = await res.text();

  let json: any;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    // retorno “envelope-like” para não quebrar UI
    return {
      data: [] as any,
      meta: { request_id: "n/a" },
      links: { self: path, next: null, prev: null },
      errors: ["Invalid JSON response"],
    };
  }

  // normaliza errors do envelope do backend
  if (json && typeof json === "object" && "errors" in json) {
    json.errors = normalizeErrors(json.errors);
  }

  // se HTTP != 2xx, ainda devolve envelope normalizado (sem throw)
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

// LIST
export async function fetchResources(
  resource: ResourceType,
  page: number,
  pageSize: number,
  q: string,
  signal?: AbortSignal
): Promise<ApiEnvelope<Resource>> {
  const query = buildQuery({
    page,
    page_size: pageSize,
    q: q?.trim() ? q.trim() : undefined,
  });

  return requestEnvelope<Resource>(`/api/${resource}${query}`, signal);
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
  const query = buildQuery({
    page,
    page_size: pageSize,
    q: q?.trim() ? q.trim() : undefined,
  });

  return requestEnvelope<RelatedItem>(`/api/${resource}/${id}/${rel}${query}`, signal);
}
