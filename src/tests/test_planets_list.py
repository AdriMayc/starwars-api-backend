import httpx
import respx

from clients.swapi import RetryConfig, SwapiClient
from app.main import create_app_router


@respx.mock
def test_planets_list_success_adds_id_and_envelope():
    respx.get(
        "https://swapi.dev/api/planets/",
        params={"page": 1},
    ).respond(
        200,
        json={
            "count": 1,
            "results": [
                {"name": "Tatooine", "url": "https://swapi.dev/api/planets/1/"},
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/planets",
        query={"page": "1"},
        headers={"x-request-id": "rid-pl1"},
        body=None,
        request_id="rid-pl1",
    )

    assert status == 200
    assert payload["errors"] == []
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["count"] == 1
    assert payload["data"][0]["id"] == 1
    assert payload["data"][0]["name"] == "Tatooine"


def test_planets_list_invalid_page_returns_400():
    router = create_app_router(swapi_client=SwapiClient(sleep_fn=lambda _: None))

    status, payload, _ = router.dispatch(
        method="GET",
        path="/planets",
        query={"page": "0"},
        headers={"x-request-id": "rid-pl2"},
        body=None,
        request_id="rid-pl2",
    )

    assert status == 400
    assert payload["errors"][0]["code"] == "VALIDATION_ERROR"


@respx.mock
def test_planets_list_timeout_returns_504():
    respx.get(
        "https://swapi.dev/api/planets/",
        params={"page": 1},
    ).side_effect = httpx.ReadTimeout("boom")

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/planets",
        query={"page": "1"},
        headers={"x-request-id": "rid-pl3"},
        body=None,
        request_id="rid-pl3",
    )

    assert status == 504
    assert payload["errors"][0]["code"] == "UPSTREAM_TIMEOUT"


@respx.mock
def test_planets_list_respects_page_size_and_links():
    respx.get(
        "https://swapi.dev/api/planets/",
        params={"page": 1},
    ).respond(
        200,
        json={
            "count": 2,
            "results": [
                {"name": "Tatooine", "url": "https://swapi.dev/api/planets/1/"},
                {"name": "Alderaan", "url": "https://swapi.dev/api/planets/2/"},
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/planets",
        query={"page": "1", "page_size": "1"},
        headers={"x-request-id": "rid-pl4"},
        body=None,
        request_id="rid-pl4",
    )

    assert status == 200
    assert payload["meta"]["page_size"] == 1
    assert payload["meta"]["count"] == 1
    assert payload["links"]["self"] == "/planets?page=1&page_size=1"
    assert payload["links"]["next"] == "/planets?page=2&page_size=1"
    assert payload["links"]["prev"] is None
    assert len(payload["data"]) == 1
    assert payload["data"][0]["id"] == 1


@respx.mock
def test_planets_list_page_size_20_fetches_multiple_pages():
    respx.get(
        "https://swapi.dev/api/planets/",
        params={"page": 1},
    ).respond(
        200,
        json={
            "count": 20,
            "results": [
                {"name": f"PL{i}", "url": f"https://swapi.dev/api/planets/{i}/"}
                for i in range(1, 11)
            ],
        },
    )

    respx.get(
        "https://swapi.dev/api/planets/",
        params={"page": 2},
    ).respond(
        200,
        json={
            "count": 20,
            "results": [
                {"name": f"PL{i}", "url": f"https://swapi.dev/api/planets/{i}/"}
                for i in range(11, 21)
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/planets",
        query={"page": "1", "page_size": "20"},
        headers={"x-request-id": "rid-pl5"},
        body=None,
        request_id="rid-pl5",
    )

    assert status == 200
    assert payload["meta"]["count"] == 20
    assert payload["meta"]["total"] == 20
    assert len(payload["data"]) == 20
