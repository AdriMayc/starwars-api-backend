import type { ApiEnvelope, ResourceType, Resource, RelatedItem } from "../types/api";

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

async function request<T>(path: string): Promise<ApiEnvelope<T>> {
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
      links: { self: path },
      errors: ["Invalid JSON response"],
    };
  }

  // Normaliza envelope do seu backend (errors pode ser objeto)
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

export function fetchResources(
  type: ResourceType,
  page = 1,
  pageSize = 10,
  query = ""
): Promise<ApiEnvelope<Resource>> {
  return request<Resource>(`/api/${type}${qs({ page, page_size: pageSize, q: query })}`);
}

export function fetchRelated(
  type: "films" | "planets",
  id: number,
  relationType: "characters" | "residents"
): Promise<ApiEnvelope<RelatedItem>> {
  return request<RelatedItem>(`/api/${type}/${id}/${relationType}`);
}
