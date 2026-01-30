import httpx
import respx
import pytest

from clients.swapi import RetryConfig, SwapiClient
from app.main import create_app_router


@respx.mock
def test_films_list_success_adds_id_and_envelope():
    respx.get("https://swapi.dev/api/films/").respond(
        200,
        json={
            "count": 1,
            "results": [
                {"title": "A New Hope", "url": "https://swapi.dev/api/films/1/"},
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _headers = router.dispatch(
        method="GET",
        path="/films",
        query={"page": "1"},
        headers={"x-request-id": "rid-1"},
        body=None,
        request_id="rid-1",
    )

    assert status == 200
    assert payload["errors"] == []
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["count"] == 1
    assert payload["data"][0]["id"] == 1
    assert payload["data"][0]["title"] == "A New Hope"


def test_films_list_invalid_page_returns_400():
    router = create_app_router(swapi_client=SwapiClient(sleep_fn=lambda _: None))

    status, payload, _headers = router.dispatch(
        method="GET",
        path="/films",
        query={"page": "0"},
        headers={"x-request-id": "rid-2"},
        body=None,
        request_id="rid-2",
    )

    assert status == 400
    assert payload["errors"][0]["code"] == "VALIDATION_ERROR"


@respx.mock
def test_films_list_timeout_returns_504():
    respx.get("https://swapi.dev/api/films/").side_effect = httpx.ReadTimeout("boom")

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _headers = router.dispatch(
        method="GET",
        path="/films",
        query={"page": "1"},
        headers={"x-request-id": "rid-3"},
        body=None,
        request_id="rid-3",
    )

    assert status == 504
    assert payload["errors"][0]["code"] == "UPSTREAM_TIMEOUT"
