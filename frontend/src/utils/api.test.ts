import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchResources, fetchRelated } from "./api";

function mockFetch(body: any, ok = true, status = 200) {
  (globalThis as any).fetch = vi.fn(async (_url: string, _opts: any) => ({
    ok,
    status,
    text: async () => JSON.stringify(body),
  }));
}

describe("api.ts", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // garante base consistente nos testes
    (import.meta as any).env = {
      ...(import.meta as any).env,
      VITE_API_BASE_URL: "http://127.0.0.1:8080",
      VITE_API_KEY: undefined,
    };
  });

  it("fetchResources: chama baseUrl/resource com query e repassa signal", async () => {
    mockFetch({
      data: [{ id: 1, title: "A New Hope", url: "x" }],
      meta: { request_id: "r1" },
      links: { self: "/films" },
      errors: [],
    });

    const ac = new AbortController();
    const r = await fetchResources("films", 1, 10, "hope", ac.signal);

    expect((globalThis as any).fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8080/films?page=1&page_size=10&q=hope",
      expect.objectContaining({ signal: ac.signal, headers: expect.any(Object) })
    );
    expect(r.data[0].id).toBe(1);
  });

  it("fetchResources: normaliza errors objeto -> string[]", async () => {
    mockFetch({
      data: [],
      meta: { request_id: "r2" },
      links: { self: "/films" },
      errors: [{ code: "UPSTREAM", message: "SWAPI down" }],
    });

    const r = await fetchResources("films", 1, 10, "");
    expect(r.errors[0]).toContain("SWAPI down");
  });

  it("fetchRelated: chama rota correta e repassa signal", async () => {
    mockFetch({
      data: [{ id: 1, name: "Luke" }],
      meta: { request_id: "r3" },
      links: { self: "/films/1/characters" },
      errors: [],
    });

    const ac = new AbortController();
    const r = await fetchRelated("films", 1, "characters", ac.signal);

    expect((globalThis as any).fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8080/films/1/characters?page=1&page_size=10",
      expect.objectContaining({ signal: ac.signal, headers: expect.any(Object) })
    );
    expect(r.data[0].name).toBe("Luke");
  });
});
