# src/tests/test_starships_list.py
import httpx
import respx

from clients.swapi import RetryConfig, SwapiClient
from app.main import create_app_router


@respx.mock
def test_starships_list_success_adds_id_and_envelope():
    respx.get(
        "https://swapi.dev/api/starships/",
        params={"page": 1},
    ).respond(
        200,
        json={
            "count": 1,
            "results": [
                {"name": "Death Star", "url": "https://swapi.dev/api/starships/9/"},
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/starships",
        query={"page": "1"},
        headers={"x-request-id": "rid-s1"},
        body=None,
        request_id="rid-s1",
    )

    assert status == 200
    assert payload["errors"] == []
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["count"] == 1
    assert payload["data"][0]["id"] == 9
    assert payload["data"][0]["name"] == "Death Star"


def test_starships_list_invalid_page_returns_400():
    router = create_app_router(swapi_client=SwapiClient(sleep_fn=lambda _: None))

    status, payload, _ = router.dispatch(
        method="GET",
        path="/starships",
        query={"page": "0"},
        headers={"x-request-id": "rid-s2"},
        body=None,
        request_id="rid-s2",
    )

    assert status == 400
    assert payload["errors"][0]["code"] == "VALIDATION_ERROR"


@respx.mock
def test_starships_list_timeout_returns_504():
    respx.get(
        "https://swapi.dev/api/starships/",
        params={"page": 1},
    ).side_effect = httpx.ReadTimeout("boom")

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/starships",
        query={"page": "1"},
        headers={"x-request-id": "rid-s3"},
        body=None,
        request_id="rid-s3",
    )

    assert status == 504
    assert payload["errors"][0]["code"] == "UPSTREAM_TIMEOUT"


@respx.mock
def test_starships_list_respects_page_size_and_links():
    respx.get(
        "https://swapi.dev/api/starships/",
        params={"page": 1},
    ).respond(
        200,
        json={
            "count": 2,
            "results": [
                {"name": "X-wing", "url": "https://swapi.dev/api/starships/12/"},
                {"name": "TIE Advanced x1", "url": "https://swapi.dev/api/starships/13/"},
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/starships",
        query={"page": "1", "page_size": "1"},
        headers={"x-request-id": "rid-s4"},
        body=None,
        request_id="rid-s4",
    )

    assert status == 200
    assert payload["meta"]["page_size"] == 1
    assert payload["meta"]["count"] == 1
    assert payload["links"]["self"] == "/starships?page=1&page_size=1"
    assert payload["links"]["next"] == "/starships?page=2&page_size=1"
    assert payload["links"]["prev"] is None
    assert len(payload["data"]) == 1
    assert payload["data"][0]["id"] == 12


@respx.mock
def test_starships_list_search_forwards_to_swapi():
    route = respx.get(
        "https://swapi.dev/api/starships/",
        params={"page": 1, "search": "falcon"},
    ).respond(
        200,
        json={
            "count": 1,
            "results": [
                {"name": "Millennium Falcon", "url": "https://swapi.dev/api/starships/10/"},
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/starships",
        query={"page": "1", "q": "falcon"},
        headers={"x-request-id": "rid-s5"},
        body=None,
        request_id="rid-s5",
    )

    assert status == 200
    assert payload["meta"]["total"] == 1

    assert route.called
    assert route.calls.last.request.url.params.get("search") == "falcon"


@respx.mock
def test_starships_list_page_size_20_fetches_multiple_pages():
    respx.get(
        "https://swapi.dev/api/starships/",
        params={"page": 1},
    ).respond(
        200,
        json={
            "count": 20,
            "results": [
                {"name": f"S{i}", "url": f"https://swapi.dev/api/starships/{i}/"}
                for i in range(1, 11)
            ],
        },
    )

    respx.get(
        "https://swapi.dev/api/starships/",
        params={"page": 2},
    ).respond(
        200,
        json={
            "count": 20,
            "results": [
                {"name": f"S{i}", "url": f"https://swapi.dev/api/starships/{i}/"}
                for i in range(11, 21)
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/starships",
        query={"page": "1", "page_size": "20"},
        headers={"x-request-id": "rid-s6"},
        body=None,
        request_id="rid-s6",
    )

    assert status == 200
    assert payload["meta"]["count"] == 20
    assert payload["meta"]["total"] == 20
    assert len(payload["data"]) == 20
