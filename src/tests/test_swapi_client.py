
import httpx
import pytest
import respx

from clients.swapi import (
    RetryConfig,
    SwapiBadResponse,
    SwapiClient,
    SwapiNotFound,
    SwapiTimeout,
    SwapiUpstreamError,
)


@respx.mock
def test_get_success_200():
    respx.get("https://swapi.dev/api/films/").respond(200, json={"count": 1})
    c = SwapiClient(sleep_fn=lambda _: None)

    data = c.get("/films/")
    assert data["count"] == 1


@respx.mock
def test_timeout_retries_then_fails():
    respx.get("https://swapi.dev/api/films/").side_effect = httpx.ReadTimeout("boom")

    c = SwapiClient(
        retry=RetryConfig(max_retries=2),
        sleep_fn=lambda _: None,
    )

    with pytest.raises(SwapiTimeout):
        c.get("/films/")


@respx.mock
def test_500_retries_then_succeeds():
    route = respx.get("https://swapi.dev/api/films/")
    route.side_effect = [
        httpx.Response(500, json={"detail": "err"}),
        httpx.Response(200, json={"ok": True}),
    ]

    c = SwapiClient(retry=RetryConfig(max_retries=2), sleep_fn=lambda _: None)
    data = c.get("/films/")
    assert data["ok"] is True


@respx.mock
def test_404_no_retry_raises_not_found():
    respx.get("https://swapi.dev/api/films/999/").respond(404, json={"detail": "nope"})

    c = SwapiClient(sleep_fn=lambda _: None)
    with pytest.raises(SwapiNotFound):
        c.get("/films/999/")


@respx.mock
def test_400_no_retry_raises_upstream_error():
    respx.get("https://swapi.dev/api/films/").respond(400, json={"detail": "bad"})

    c = SwapiClient(sleep_fn=lambda _: None)
    with pytest.raises(SwapiUpstreamError):
        c.get("/films/")


@respx.mock
def test_invalid_json_raises_bad_response():
    # retorna texto inválido para json()
    respx.get("https://swapi.dev/api/films/").respond(200, text="not-json")

    c = SwapiClient(sleep_fn=lambda _: None)
    with pytest.raises(SwapiBadResponse):
        c.get("/films/")
