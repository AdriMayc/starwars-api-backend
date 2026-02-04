import respx

from clients.swapi import RetryConfig, SwapiClient
from app.main import create_app_router


@respx.mock
def test_starships_page_size_50_page_1_returns_all_and_next_null_when_upstream_404_after_last_page():
    # starships total=36 => páginas 1..4 ok, 5 -> 404
    total = 36

    for page in range(1, 5):
        start = (page - 1) * 10 + 1
        end = min(page * 10, total)
        respx.get("https://swapi.dev/api/starships/", params={"page": page}).respond(
            200,
            json={
                "count": total,
                "results": [
                    {"name": f"S{i}", "url": f"https://swapi.dev/api/starships/{i}/"}
                    for i in range(start, end + 1)
                ],
            },
        )

    respx.get("https://swapi.dev/api/starships/", params={"page": 5}).respond(404)

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None)
    router = create_app_router(swapi_client=client)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/starships",
        query={"page": "1", "page_size": "50"},
        headers={"x-request-id": "rid-s1"},
        body=None,
        request_id="rid-s1",
    )

    assert status == 200
    assert payload["meta"]["total"] == 36
    assert payload["meta"]["count"] == 36
    assert payload["links"]["next"] is None
    assert payload["links"]["prev"] is None
    assert len(payload["data"]) == 36
