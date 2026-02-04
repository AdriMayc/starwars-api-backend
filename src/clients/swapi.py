# src/clients/swapi.py
from __future__ import annotations

import time
from dataclasses import dataclass
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
    max_retries: int = 2          # total de tentativas extras (além da 1ª)
    backoff_base: float = 0.2     # segundos
    backoff_factor: float = 2.0   # exponencial: base * factor^attempt
    retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504)


@dataclass
class SwapiClient:
    base_url: str = "https://swapi.dev/api"
    timeout: float = 3.0
    retry: RetryConfig = RetryConfig()
    sleep_fn: Callable[[float], None] = time.sleep

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=httpx.Timeout(self.timeout),
            headers={"Accept": "application/json"},
        )

    def get(self, resource: str, params: Mapping[str, Any] | None = None) -> JsonDict:
        path = resource.strip()
        if not path.startswith("/"):
            path = "/" + path
        return self._request("GET", path, params=params)

    def get_by_url(self, url: str, params: Mapping[str, Any] | None = None) -> JsonDict:
        # Para URLs absolutas fornecidas pela SWAPI (ex.: film.characters[])
        return self._request("GET", url, params=params, absolute=True)

    def _request(
        self,
        method: str,
        url_or_path: str,
        *,
        params: Mapping[str, Any] | None,
        absolute: bool = False,
    ) -> JsonDict:
        attempt = 0
        last_exc: Exception | None = None

        # total de tentativas = 1 + max_retries
        for attempt in range(0, self.retry.max_retries + 1):
            try:
                with self._client() as c:
                    if absolute:
                        resp = c.request(method, url_or_path, params=params)
                    else:
                        resp = c.request(method, url_or_path, params=params)

                # 404: não retry
                if resp.status_code == 404:
                    raise SwapiNotFound(f"SWAPI 404 for {resp.request.url}")

                # 4xx (exceto 429) não retry
                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    raise SwapiUpstreamError(f"SWAPI returned {resp.status_code}")

                # retry em status selecionados
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
                # 404 nunca retry
                raise

            except SwapiUpstreamError as e:
                last_exc = e
                # se não é retryable, já teria sido levantado acima como 4xx não-429
                if attempt >= self.retry.max_retries:
                    raise

            # backoff entre tentativas (não dorme após a última)
            if attempt < self.retry.max_retries:
                delay = self.retry.backoff_base * (self.retry.backoff_factor ** attempt)
                self.sleep_fn(delay)

        # fallback (não deve chegar aqui)
        raise SwapiError("Unexpected SWAPI client failure") from last_exc


    def get_films(self, search: str | None = None) -> JsonDict:
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        return self.get("/films/", params=params or None)

    def get_people(self, search: str | None = None) -> JsonDict:
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        return self.get("/people/", params=params or None)

    def get_planets(self, search: str | None = None) -> JsonDict:
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        return self.get("/planets/", params=params or None)