import type { ApiEnvelope, RelatedItem } from "../types/api";

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    const s = String(v).trim();
    if (!s) continue;
    sp.set(k, s);
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
}

function normalizeErrors(errors: unknown): string[] {
  if (!errors) return [];
  if (Array.isArray(errors)) {
    return errors.map((e: any) => {
      if (typeof e === "string") return e;
      if (e?.message) return String(e.message);
      if (e?.code) return String(e.code);
      return "Unknown error";
    });
  }
  return ["Unknown error"];
}

function baseUrl() {
  // evita // e aceita vazio (ex.: proxy /api)
  const raw = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
  return raw.replace(/\/+$/, "");
}

async function request<T>(
  path: string,
  opts?: { signal?: AbortSignal }
): Promise<ApiEnvelope<T>> {
  const apiKey = import.meta.env.VITE_API_KEY as string | undefined;

  const headers: Record<string, string> = { accept: "application/json" };
  if (apiKey) headers["x-api-key"] = apiKey;

  const res = await fetch(path, { headers, signal: opts?.signal });

  const text = await res.text();

  let json: any;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    return {
      data: [] as any,
      meta: { request_id: "n/a" },
      links: { self: path },
      errors: ["Invalid JSON response"],
    };
  }

  // Normaliza envelope do backend (errors pode vir como objeto)
  if (json && typeof json === "object" && "errors" in json) {
    json.errors = normalizeErrors(json.errors);
  }

  if (!res.ok) {
    const reqId = json?.meta?.request_id ?? "n/a";
    return {
      data: [] as any,
      meta: { request_id: reqId },
      links: { self: path },
      errors: [json?.message ?? `HTTP ${res.status}`],
    };
  }

  return json as ApiEnvelope<T>;
}

export async function fetchResources(
  resource: string,
  page: number,
  pageSize: number,
  q: string,
  signal?: AbortSignal
): Promise<ApiEnvelope<any>> {
  const url =
    `${baseUrl()}/${resource}` +
    qs({
      page,
      page_size: pageSize,
      q: q?.trim() || undefined,
    });

  return request(url, { signal });
}

export async function fetchRelated(
  resource: "films" | "planets",
  id: number,
  rel: "characters" | "residents",
  signal?: AbortSignal
): Promise<ApiEnvelope<RelatedItem>> {
  const url =
    `${baseUrl()}/${resource}/${id}/${rel}` +
    qs({ page: 1, page_size: 10 });

  return request(url, { signal });
}
