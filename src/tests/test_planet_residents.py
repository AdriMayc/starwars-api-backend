import httpx
import respx

from app.main import create_app_router
from clients.swapi import RetryConfig, SwapiClient


@respx.mock
def test_planet_residents_success_envelope_and_ids():
    respx.get("https://swapi.dev/api/planets/1/").respond(
        200,
        json={
            "name": "Tatooine",
            "residents": [
                "https://swapi.dev/api/people/1/",
                "https://swapi.dev/api/people/2/",
            ],
            "url": "https://swapi.dev/api/planets/1/",
        },
    )
    respx.get("https://swapi.dev/api/people/1/").respond(
        200, json={"name": "Luke Skywalker", "url": "https://swapi.dev/api/people/1/"}
    )
    respx.get("https://swapi.dev/api/people/2/").respond(
        200, json={"name": "C-3PO", "url": "https://swapi.dev/api/people/2/"}
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/planets/1/residents",
        query={"page": "1"},
        headers={"x-request-id": "rid-pr-1"},
        body=None,
        request_id="rid-pr-1",
    )

    assert status == 200
    assert payload["errors"] == []
    assert payload["meta"]["count"] == 2
    assert payload["data"][0]["id"] == 1
    assert payload["links"]["self"] == "/planets/1/residents?page=1&page_size=10"


def test_planet_residents_invalid_page_returns_400():
    router = create_app_router(swapi_client=SwapiClient(sleep_fn=lambda _: None))

    status, payload, _ = router.dispatch(
        method="GET",
        path="/planets/1/residents",
        query={"page": "0"},
        headers={"x-request-id": "rid-pr-2"},
        body=None,
        request_id="rid-pr-2",
    )

    assert status == 400
    assert payload["errors"][0]["code"] == "VALIDATION_ERROR"


@respx.mock
def test_planet_residents_timeout_returns_504():
    respx.get("https://swapi.dev/api/planets/1/").respond(
        200, json={"residents": ["https://swapi.dev/api/people/1/"]}
    )
    respx.get("https://swapi.dev/api/people/1/").side_effect = httpx.ReadTimeout("boom")

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/planets/1/residents",
        query={"page": "1"},
        headers={"x-request-id": "rid-pr-3"},
        body=None,
        request_id="rid-pr-3",
    )

    assert status == 504
    assert payload["errors"][0]["code"] == "UPSTREAM_TIMEOUT"
