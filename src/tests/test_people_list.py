import httpx
import respx

from clients.swapi import RetryConfig, SwapiClient
from app.main import create_app_router


@respx.mock
def test_people_list_success_adds_id_and_envelope():
    respx.get("https://swapi.dev/api/people/").respond(
        200,
        json={
            "count": 1,
            "results": [
                {"name": "Luke Skywalker", "url": "https://swapi.dev/api/people/1/"},
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/people",
        query={"page": "1"},
        headers={"x-request-id": "rid-p1"},
        body=None,
        request_id="rid-p1",
    )

    assert status == 200
    assert payload["errors"] == []
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["count"] == 1
    assert payload["data"][0]["id"] == 1
    assert payload["data"][0]["name"] == "Luke Skywalker"


def test_people_list_invalid_page_returns_400():
    router = create_app_router(swapi_client=SwapiClient(sleep_fn=lambda _: None))

    status, payload, _ = router.dispatch(
        method="GET",
        path="/people",
        query={"page": "0"},
        headers={"x-request-id": "rid-p2"},
        body=None,
        request_id="rid-p2",
    )

    assert status == 400
    assert payload["errors"][0]["code"] == "VALIDATION_ERROR"


@respx.mock
def test_people_list_timeout_returns_504():
    respx.get("https://swapi.dev/api/people/").side_effect = httpx.ReadTimeout("boom")

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/people",
        query={"page": "1"},
        headers={"x-request-id": "rid-p3"},
        body=None,
        request_id="rid-p3",
    )

    assert status == 504
    assert payload["errors"][0]["code"] == "UPSTREAM_TIMEOUT"


@respx.mock
def test_people_list_respects_page_size_and_links():
    respx.get("https://swapi.dev/api/people/").respond(
        200,
        json={
            "count": 2,
            "results": [
                {"name": "Luke Skywalker", "url": "https://swapi.dev/api/people/1/"},
                {"name": "C-3PO", "url": "https://swapi.dev/api/people/2/"},
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/people",
        query={"page": "1", "page_size": "1"},
        headers={"x-request-id": "rid-p4"},
        body=None,
        request_id="rid-p4",
    )

    assert status == 200
    assert payload["meta"]["page_size"] == 1
    assert payload["meta"]["count"] == 1
    assert payload["links"]["self"] == "/people?page=1&page_size=1"
    assert payload["links"]["next"] == "/people?page=2&page_size=1"
    assert payload["links"]["prev"] is None
    assert len(payload["data"]) == 1
    assert payload["data"][0]["id"] == 1
