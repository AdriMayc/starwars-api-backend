# src/clients/swapi.py
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

import httpx

JsonDict = dict[str, Any]


class SwapiError(Exception):
    """Base para erros do client SWAPI."""


class SwapiTimeout(SwapiError):
    """Timeout ao chamar SWAPI."""


class SwapiUpstreamError(SwapiError):
    """SWAPI retornou erro 5xx ou 429 de forma não recuperável."""


class SwapiBadResponse(SwapiError):
    """Resposta inválida (ex.: JSON malformado)."""


class SwapiNotFound(SwapiError):
    """Recurso inexistente (404) — útil para mapear em 404 na nossa API depois."""


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int = 2
    backoff_base: float = 0.2
    backoff_factor: float = 2.0
    retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504)


@dataclass
class _TtlCache:
    ttl_seconds: float
    now_fn: Callable[[], float]
    _store: dict[str, tuple[float, JsonDict]] = field(default_factory=dict)

    def get(self, key: str) -> JsonDict | None:
        item = self._store.get(key)
        if not item:
            return None
        ts, val = item
        if (self.now_fn() - ts) > self.ttl_seconds:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, val: JsonDict) -> None:
        self._store[key] = (self.now_fn(), val)

    def clear(self) -> None:
        self._store.clear()


@dataclass
class SwapiClient:
    base_url: str = "https://swapi.dev/api"
    timeout: float = 3.0
    retry: RetryConfig = RetryConfig()
    sleep_fn: Callable[[float], None] = time.sleep

    # cache TTL (em segundos) para get_by_url (characters/residents)
    by_url_cache_ttl: float = 300.0  # 5 min (ajuste)
    now_fn: Callable[[], float] = time.time

    _http: httpx.Client | None = field(default=None, init=False, repr=False)
    _by_url_cache: _TtlCache | None = field(default=None, init=False, repr=False)

    def _get_client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(
                base_url=self.base_url.rstrip("/"),
                timeout=httpx.Timeout(self.timeout),
                headers={"Accept": "application/json"},
            )
        return self._http

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def _get_by_url_cache(self) -> _TtlCache:
        if self._by_url_cache is None:
            self._by_url_cache = _TtlCache(ttl_seconds=self.by_url_cache_ttl, now_fn=self.now_fn)
        return self._by_url_cache

    def get(self, resource: str, params: Mapping[str, Any] | None = None) -> JsonDict:
        # normaliza: nunca depender do caller passar / no início
        path = (resource or "").strip().lstrip("/")
        if not path.endswith("/"):
            path += "/"
        return self._request("GET", f"/{path}", params=params, absolute=False)

    def get_by_url(self, url: str, params: Mapping[str, Any] | None = None) -> JsonDict:
        # cache por URL absoluta + params (params quase sempre None aqui)
        cache = self._get_by_url_cache()
        key = f"url={url}|params={tuple(sorted((params or {}).items()))}"
        cached = cache.get(key)
        if cached is not None:
            return cached

        data = self._request("GET", url, params=params, absolute=True)
        cache.set(key, data)
        return data

    def _request(
        self,
        method: str,
        url_or_path: str,
        *,
        params: Mapping[str, Any] | None,
        absolute: bool = False,
    ) -> JsonDict:
        last_exc: Exception | None = None

        for attempt in range(0, self.retry.max_retries + 1):
            try:
                c = self._get_client()
                resp = c.request(method, url_or_path, params=params)

                if resp.status_code == 404:
                    raise SwapiNotFound(f"SWAPI 404 for {resp.request.url}")

                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    raise SwapiUpstreamError(f"SWAPI returned {resp.status_code}")

                if resp.status_code in self.retry.retry_on_status:
                    raise SwapiUpstreamError(f"SWAPI returned {resp.status_code}")

                try:
                    return resp.json()
                except ValueError as e:
                    raise SwapiBadResponse("Invalid JSON from SWAPI") from e

            except httpx.TimeoutException as e:
                last_exc = e
                if attempt >= self.retry.max_retries:
                    raise SwapiTimeout("Timeout calling SWAPI") from e

            except SwapiNotFound:
                raise

            except SwapiUpstreamError as e:
                last_exc = e
                if attempt >= self.retry.max_retries:
                    raise

            if attempt < self.retry.max_retries:
                delay = self.retry.backoff_base * (self.retry.backoff_factor ** attempt)
                self.sleep_fn(delay)

        raise SwapiError("Unexpected SWAPI client failure") from last_exc
