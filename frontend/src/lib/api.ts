import type { Envelope, Resource, Film, Person, Planet, Starship } from "../types/api";

export type ListResponseMap = {
  films: Film[];
  people: Person[];
  planets: Planet[];
  starships: Starship[];
};

export type RelatedResponseMap = {
  filmCharacters: Person[];
  planetResidents: Person[];
};

export type ListQuery = {
  page?: number;
  page_size?: number;
  q?: string;
};

function buildQuery(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    const s = String(v).trim();
    if (!s) continue;
    sp.set(k, s);
  }
  return sp.toString();
}

export class ApiError extends Error {
  status: number;
  requestId?: string;
  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
  }
}

async function requestJson<T>(path: string, query?: Record<string, unknown>, signal?: AbortSignal): Promise<Envelope<T>> {
  const qs = query ? buildQuery(query) : "";
  const url = qs ? `${path}?${qs}` : path;

  const res = await fetch(url, {
    method: "GET",
    headers: { "accept": "application/json" },
    signal,
  });

  const text = await res.text();
  let json: unknown;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    throw new ApiError("Resposta inválida (JSON malformado).", res.status);
  }

  if (!res.ok) {
    // tenta extrair request_id se vier no envelope
    const reqId = (json as any)?.meta?.request_id;
    throw new ApiError(`HTTP ${res.status}`, res.status, reqId);
  }

  const env = json as Envelope<T>;

  if (env?.errors?.length) {
    const reqId = env?.meta?.request_id;
    const msg = env.errors.map((e) => e.message || e.code).filter(Boolean).join(" | ") || "Erro da API";
    throw new ApiError(msg, res.status, reqId);
  }

  return env;
}

// LISTAS
export function listResource<R extends Resource>(resource: R, query?: ListQuery, signal?: AbortSignal) {
  return requestJson<ListResponseMap[R]>(`/api/${resource}`, query, signal);
}

// RELACIONADOS
export function listFilmCharacters(id: number, query?: ListQuery, signal?: AbortSignal) {
  return requestJson<RelatedResponseMap["filmCharacters"]>(`/api/films/${id}/characters`, query, signal);
}

export function listPlanetResidents(id: number, query?: ListQuery, signal?: AbortSignal) {
  return requestJson<RelatedResponseMap["planetResidents"]>(`/api/planets/${id}/residents`, query, signal);
}
