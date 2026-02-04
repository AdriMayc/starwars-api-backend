import respx
import httpx

from clients.swapi import SwapiClient
from app.swapi_window import fetch_window


@respx.mock
def test_fetch_window_two_pages():
    client = SwapiClient()

    respx.get("https://swapi.dev/api/people/").respond(
        200,
        json={
            "count": 20,
            "results": [{"name": f"P{i}", "url": f"/p/{i}"} for i in range(10)],
        },
    )

    respx.get("https://swapi.dev/api/people/").respond(
        200,
        json={
            "count": 20,
            "results": [{"name": f"P{i}", "url": f"/p/{i}"} for i in range(10, 20)],
        },
    )

    items, total = fetch_window(client, "/people/", page=1, page_size=20)

    assert len(items) == 20
    assert total == 20

@respx.mock
def test_fetch_window_stops_on_404_page_out_of_range():
    client = SwapiClient()

    respx.get("https://swapi.dev/api/people/", params={"page": 1}).respond(
        200,
        json={
            "count": 20,
            "results": [{"name": f"P{i}", "url": f"/p/{i}"} for i in range(10)],
        },
    )

    respx.get("https://swapi.dev/api/people/", params={"page": 2}).respond(
        200,
        json={
            "count": 20,
            "results": [{"name": f"P{i}", "url": f"/p/{i}"} for i in range(10, 20)],
        },
    )

    # SWAPI costuma responder 404 quando page > último.
    respx.get("https://swapi.dev/api/people/", params={"page": 3}).respond(404)

    items, total = fetch_window(client, "/people/", page=1, page_size=25)

    assert total == 20
    assert len(items) == 20
