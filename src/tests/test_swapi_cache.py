import respx
from httpx import Response

from clients.swapi import RetryConfig, SwapiClient
from app.main import create_app_router

@respx.mock
def test_get_by_url_is_cached_within_ttl():
    url = "https://swapi.dev/api/people/1/"
    route = respx.get(url).mock(return_value=Response(200, json={"name": "Luke"}))

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None, by_url_cache_ttl=300.0)

    a = client.get_by_url(url, params=None)
    b = client.get_by_url(url, params=None)

    assert a["name"] == "Luke"
    assert b["name"] == "Luke"
    assert route.call_count == 1  # <- só 1 chamada upstream

@respx.mock
def test_film_characters_second_call_reuses_people_cache():
    respx.get("https://swapi.dev/api/films/1/").respond(
        200,
        json={"characters": ["https://swapi.dev/api/people/1/", "https://swapi.dev/api/people/2/"]},
    )

    p1 = respx.get("https://swapi.dev/api/people/1/").respond(200, json={"name": "P1", "url": "https://swapi.dev/api/people/1/"})
    p2 = respx.get("https://swapi.dev/api/people/2/").respond(200, json={"name": "P2", "url": "https://swapi.dev/api/people/2/"})

    client = SwapiClient(retry=RetryConfig(max_retries=0), sleep_fn=lambda _: None, by_url_cache_ttl=300.0)
    router = create_app_router(swapi_client=client)

    # 1ª chamada: faz fan-out
    status1, payload1, _ = router.dispatch(
        method="GET",
        path="/films/1/characters",
        query={"page": "1", "page_size": "10"},
        headers={"x-request-id": "rid-1"},
        body=None,
        request_id="rid-1",
    )
    assert status1 == 200
    assert payload1["meta"]["count"] == 2

    # 2ª chamada: filme ainda é buscado, mas people devem vir do cache
    status2, payload2, _ = router.dispatch(
        method="GET",
        path="/films/1/characters",
        query={"page": "1", "page_size": "10"},
        headers={"x-request-id": "rid-2"},
        body=None,
        request_id="rid-2",
    )
    assert status2 == 200
    assert payload2["meta"]["count"] == 2

    assert p1.call_count == 1
    assert p2.call_count == 1