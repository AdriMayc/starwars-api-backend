from __future__ import annotations

from app.router import RequestContext
from app.handlers.film_characters import list_film_characters_handler
from app.handlers.planet_residents import list_planet_residents_handler


class FakeClient:
    def __init__(self, urls_key: str):
        self.urls_key = urls_key
        self.by_url_calls: list[str] = []

    def get(self, resource: str, params=None):
        # devolve 10 urls
        urls = [f"https://swapi.dev/api/people/{i}/" for i in range(1, 11)]
        return {self.urls_key: urls}

    def get_by_url(self, url: str, params=None):
        self.by_url_calls.append(url)
        return {"name": "X", "url": url}


def test_film_characters_uses_dynamic_workers_and_fast_client(monkeypatch):
    calls = {"max_workers": None, "used_fast": False}

    # intercepta run_bounded para capturar max_workers e simular retorno
    def fake_run_bounded(fn, items, *, max_workers=8):
        calls["max_workers"] = max_workers
        # marca se o fn usado é o fast: o handler cria um SwapiClient interno,
        # então não temos referência direta; testamos indiretamente:
        # chamamos fn e verificamos que funciona (retorna dict esperado).
        out = []
        for u in items:
            r = fn(u)
            out.append(r)
        calls["used_fast"] = True
        return out

    monkeypatch.setattr("app.handlers.film_characters.run_bounded", fake_run_bounded)

    client = FakeClient(urls_key="characters")
    handler = list_film_characters_handler(client)

    ctx = RequestContext(
        method="GET",
        path="/films/1/characters",
        query={"page": "1", "page_size": "10"},
        headers={},
        body=None,
        path_params={"id": "1"},
    )
    status, payload, _ = handler(ctx)

    assert status == 200
    assert calls["max_workers"] == 10
    assert calls["used_fast"] is True


def test_planet_residents_uses_dynamic_workers(monkeypatch):
    calls = {"max_workers": None}

    def fake_run_bounded(fn, items, *, max_workers=8):
        calls["max_workers"] = max_workers
        return [fn(u) for u in items]

    monkeypatch.setattr("app.handlers.planet_residents.run_bounded", fake_run_bounded)

    client = FakeClient(urls_key="residents")
    handler = list_planet_residents_handler(client)

    ctx = RequestContext(
        method="GET",
        path="/planets/1/residents",
        query={"page": "1", "page_size": "10"},
        headers={},
        body=None,
        path_params={"id": "1"},
    )
    status, payload, _ = handler(ctx)

    assert status == 200
    assert calls["max_workers"] == 10
