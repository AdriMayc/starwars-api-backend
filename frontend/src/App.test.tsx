import { render, screen, fireEvent, within } from "@testing-library/react";
import App from "./App";
import { describe, it, expect, vi, beforeEach } from "vitest";

function mockFetchSequence(responses: Array<{ ok: boolean; status: number; body: any }>) {
  let i = 0;
  (globalThis as any).fetch = vi.fn(async () => {
    const r = responses[i++] ?? responses[responses.length - 1];
    return {
      ok: r.ok,
      status: r.status,
      text: async () => JSON.stringify(r.body),
    };
  });
}

describe("App (smoke)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (import.meta as any).env = {
      ...(import.meta as any).env,
      VITE_API_BASE_URL: "http://127.0.0.1:8080",
      VITE_API_KEY: undefined,
    };
  });

  it("renders and loads films list, selects an item", async () => {
    mockFetchSequence([
      {
        ok: true,
        status: 200,
        body: {
          data: [{ id: 1, title: "A New Hope", url: "x" }],
          meta: { request_id: "r1" },
          links: { self: "/films", next: null, prev: null },
          errors: [],
        },
      },
      {
        ok: true,
        status: 200,
        body: {
          data: [{ id: 1, name: "Luke Skywalker" }],
          meta: { request_id: "r2" },
          links: { self: "/films/1/characters", next: null, prev: null },
          errors: [],
        },
      },
    ]);

    render(<App />);

    fireEvent.click((await screen.findAllByText("A New Hope"))[0]);

    const basicInfo = await screen.findByTestId("basic-info");
    expect(within(basicInfo).getByText(/A New Hope/i)).toBeInTheDocument();
  });
});
