import httpx
import respx

from clients.swapi import RetryConfig, SwapiClient
from app.main import create_app_router


def mock_swapi_people_page(respx, page: int, total: int = 82):
    base = "https://swapi.dev/api/people/"
    start = (page - 1) * 10 + 1
    end = min(page * 10, total)

    if start > total:
        # página fora do range -> SWAPI costuma responder 404
        respx.get(base, params={"page": page}).respond(404)
        return

    respx.get(base, params={"page": page}).respond(
        200,
        json={
            "count": total,
            "results": [
                {"name": f"P{i}", "url": f"https://swapi.dev/api/people/{i}/"}
                for i in range(start, end + 1)
            ],
        },
    )


@respx.mock
def test_people_list_success_adds_id_and_envelope():
    respx.get(
    "https://swapi.dev/api/people/",
    params={"page": 1},
).respond(
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
    respx.get(
        "https://swapi.dev/api/people/",
        params={"page": 1},
    ).respond(
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


@respx.mock
def test_people_list_page_size_20_fetches_multiple_pages():
    respx.get(
        "https://swapi.dev/api/people/",
        params={"page": 1},
    ).respond(
        200,
        json={
            "count": 20,
            "results": [
                {"name": f"P{i}", "url": f"https://swapi.dev/api/people/{i}/"}
                for i in range(1, 11)
            ],
        },
    )

    respx.get(
        "https://swapi.dev/api/people/",
        params={"page": 2},
    ).respond(
        200,
        json={
            "count": 20,
            "results": [
                {"name": f"P{i}", "url": f"https://swapi.dev/api/people/{i}/"}
                for i in range(11, 21)
            ],
        },
    )

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/people",
        query={"page": "1", "page_size": "20"},
        headers={"x-request-id": "rid-p5"},
        body=None,
        request_id="rid-p5",
    )

    assert status == 200
    assert payload["meta"]["count"] == 20
    assert payload["meta"]["total"] == 20
    assert len(payload["data"]) == 20

@respx.mock
def test_people_list_page_size_50_page_2_handles_swapi_404_on_page_10():
    # page=2,page_size=50 -> precisa buscar páginas 6..10 (SWAPI fixa em 10)
    total = 82

    for up_page in range(6, 11):  # 6..10
        mock_swapi_people_page(respx, up_page, total=total)

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/people",
        query={"page": "2", "page_size": "50"},
        headers={"x-request-id": "rid-p6"},
        body=None,
        request_id="rid-p6",
    )

    assert status == 200
    assert payload["meta"]["page"] == 2
    assert payload["meta"]["page_size"] == 50
    assert payload["meta"]["total"] == 82
    assert payload["meta"]["count"] == 32
    assert len(payload["data"]) == 32
    assert payload["links"]["prev"] == "/people?page=1&page_size=50"
    assert payload["links"]["next"] is None
