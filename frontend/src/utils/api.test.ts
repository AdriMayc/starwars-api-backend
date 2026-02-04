import { describe, it, expect, vi, beforeEach } from "vitest";

function makeEnvelope(data: any[] = []) {
  return {
    data,
    meta: { request_id: "rid" },
    links: { self: "/x", next: null, prev: null },
    errors: [],
  };
}

describe("api cache/dedupe", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("caches: second call to same path should not call fetch again", async () => {
    vi.resetModules();

    const fetchMock = vi.fn(async () => {
      return {
        ok: true,
        status: 200,
        text: async () => JSON.stringify(makeEnvelope([{ id: 1 }])),
      } as any;
    });

    (globalThis as any).fetch = fetchMock;

    const mod = await import("./api");
    const { fetchResources } = mod;

    const r1 = await fetchResources("people", 1, 10, "");
    const r2 = await fetchResources("people", 1, 10, "");

    expect(r1.data).toEqual([{ id: 1 }]);
    expect(r2.data).toEqual([{ id: 1 }]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("dedupes: concurrent calls to same path should share a single fetch", async () => {
    vi.resetModules();

    let resolveFetch!: (v: any) => void;
    const fetchPromise = new Promise((resolve) => {
      resolveFetch = resolve;
    });

    const fetchMock = vi.fn(() => fetchPromise as any);
    (globalThis as any).fetch = fetchMock;

    const mod = await import("./api");
    const { fetchResources } = mod;

    const p1 = fetchResources("people", 1, 10, "");
    const p2 = fetchResources("people", 1, 10, "");

    // libera o fetch depois de registrar as duas chamadas
    resolveFetch({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(makeEnvelope([{ id: 2 }])),
    });

    const [r1, r2] = await Promise.all([p1, p2]);

    expect(r1.data).toEqual([{ id: 2 }]);
    expect(r2.data).toEqual([{ id: 2 }]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("abort is per-consumer: aborting one consumer rejects with AbortError, but fetch continues and can populate cache", async () => {
    vi.resetModules();

    let resolveFetch!: (v: any) => void;
    const fetchPromise = new Promise((resolve) => {
      resolveFetch = resolve;
    });

    const fetchMock = vi.fn(() => fetchPromise as any);
    (globalThis as any).fetch = fetchMock;

    const mod = await import("./api");
    const { fetchResources } = mod;

    const ac = new AbortController();

    const pAborted = fetchResources("people", 1, 10, "", ac.signal);
    const pNormal = fetchResources("people", 1, 10, ""); // sem signal

    ac.abort();

    // primeiro deve abortar
    await expect(pAborted).rejects.toMatchObject({ name: "AbortError" });

    // agora resolvemos o fetch compartilhado
    resolveFetch({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(makeEnvelope([{ id: 3 }])),
    });

    const okResult = await pNormal;
    expect(okResult.data).toEqual([{ id: 3 }]);

    // fetch foi chamado uma vez só (dedupe)
    expect(fetchMock).toHaveBeenCalledTimes(1);

    // e a chamada subsequente deve vir do cache
    const r3 = await fetchResources("people", 1, 10, "");
    expect(r3.data).toEqual([{ id: 3 }]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
