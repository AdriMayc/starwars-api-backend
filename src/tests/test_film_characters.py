import httpx
import respx

from app.main import create_app_router
from clients.swapi import RetryConfig, SwapiClient


@respx.mock
def test_film_characters_success_envelope_and_ids():
    respx.get("https://swapi.dev/api/films/1/").respond(
        200,
        json={
            "title": "A New Hope",
            "characters": [
                "https://swapi.dev/api/people/1/",
                "https://swapi.dev/api/people/2/",
            ],
            "url": "https://swapi.dev/api/films/1/",
        },
    )
    respx.get("https://swapi.dev/api/people/1/").respond(
        200,
        json={"name": "Luke Skywalker", "url": "https://swapi.dev/api/people/1/"},
    )
    respx.get("https://swapi.dev/api/people/2/").respond(
        200,
        json={"name": "C-3PO", "url": "https://swapi.dev/api/people/2/"},
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/films/1/characters",
        query={"page": "1"},
        headers={"x-request-id": "rid-fc-1"},
        body=None,
        request_id="rid-fc-1",
    )

    assert status == 200
    assert payload["errors"] == []
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["count"] == 2
    assert payload["data"][0]["id"] == 1
    assert payload["data"][1]["id"] == 2
    assert payload["links"]["self"] == "/films/1/characters?page=1&page_size=10"


@respx.mock
def test_film_characters_respects_page_size_and_links():
    respx.get("https://swapi.dev/api/films/1/").respond(
        200,
        json={
            "characters": [
                "https://swapi.dev/api/people/1/",
                "https://swapi.dev/api/people/2/",
                "https://swapi.dev/api/people/3/",
            ]
        },
    )
    for i in (1, 2, 3):
        respx.get(f"https://swapi.dev/api/people/{i}/").respond(
            200, json={"name": f"P{i}", "url": f"https://swapi.dev/api/people/{i}/"}
        )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/films/1/characters",
        query={"page": "1", "page_size": "2"},
        headers={"x-request-id": "rid-fc-2"},
        body=None,
        request_id="rid-fc-2",
    )

    assert status == 200
    assert payload["meta"]["page_size"] == 2
    assert payload["meta"]["count"] == 2
    assert payload["meta"]["total"] == 3
    assert payload["links"]["next"] == "/films/1/characters?page=2&page_size=2"
    assert payload["links"]["prev"] is None


def test_film_characters_invalid_page_returns_400():
    router = create_app_router(swapi_client=SwapiClient(sleep_fn=lambda _: None))

    status, payload, _ = router.dispatch(
        method="GET",
        path="/films/1/characters",
        query={"page": "0"},
        headers={"x-request-id": "rid-fc-3"},
        body=None,
        request_id="rid-fc-3",
    )

    assert status == 400
    assert payload["errors"][0]["code"] == "VALIDATION_ERROR"


@respx.mock
def test_film_characters_timeout_returns_504():
    respx.get("https://swapi.dev/api/films/1/").respond(
        200,
        json={"characters": ["https://swapi.dev/api/people/1/"]},
    )
    respx.get("https://swapi.dev/api/people/1/").side_effect = httpx.ReadTimeout("boom")

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/films/1/characters",
        query={"page": "1"},
        headers={"x-request-id": "rid-fc-4"},
        body=None,
        request_id="rid-fc-4",
    )

    assert status == 504
    assert payload["errors"][0]["code"] == "UPSTREAM_TIMEOUT"
