import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchResources, fetchRelated } from "./api";

function mockFetch(body: any, ok = true, status = 200) {
  (globalThis as any).fetch = vi.fn(async () => ({
    ok,
    status,
    text: async () => JSON.stringify(body),
  }));
}

describe("api.ts", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("fetchResources: chama /api/films com query", async () => {
    mockFetch({
      data: [{ id: 1, title: "A New Hope", url: "x" }],
      meta: { request_id: "r1" },
      links: { self: "/films", next: null, prev: null },
      errors: [],
    });

    const r = await fetchResources("films", 1, 10, "hope");
    expect((globalThis as any).fetch).toHaveBeenCalledWith(
      "/api/films?page=1&page_size=10&q=hope",
      expect.any(Object)
    );
    expect(r.data[0].id).toBe(1);
  });

  it("fetchResources: normaliza errors objeto -> string[]", async () => {
    mockFetch({
      data: [],
      meta: { request_id: "r2" },
      links: { self: "/films", next: null, prev: null },
      errors: [{ code: "UPSTREAM", message: "SWAPI down" }],
    });

    const r = await fetchResources("films", 1, 10, "");
    expect(r.errors[0]).toContain("SWAPI down");
  });

  it("fetchRelated: chama rota correta", async () => {
    mockFetch({
      data: [{ id: 1, name: "Luke" }],
      meta: { request_id: "r3" },
      links: { self: "/films/1/characters", next: null, prev: null },
      errors: [],
    });

    const r = await fetchRelated("films", 1, "characters");
    expect((globalThis as any).fetch).toHaveBeenCalledWith(
      "/api/films/1/characters?page=1&page_size=10",
      expect.any(Object)
    );
    expect(r.data[0].name).toBe("Luke");
  });
});

