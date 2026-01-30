from __future__ import annotations

from typing import Any, Mapping

from clients.swapi import (
    SwapiBadResponse,
    SwapiClient,
    SwapiNotFound,
    SwapiTimeout,
    SwapiUpstreamError,
)
from clients.utils import attach_id
from schemas.common import ErrorItem, fail, ok
from app.router import RequestContext


def _self_url(path: str, query: Mapping[str, Any]) -> str:
    # monta self básico (sem depender de request host)
    if not query:
        return path
    parts = []
    for k, v in query.items():
        if v is None:
            continue
        parts.append(f"{k}={v}")
    qs = "&".join(parts)
    return f"{path}?{qs}" if qs else path


def list_films_handler(client: SwapiClient):
    def handler(ctx: RequestContext):
        # --- validação simples de query ---
        raw_page = ctx.query.get("page", 1)
        q = ctx.query.get("q")

        try:
            page = int(raw_page)
        except (TypeError, ValueError):
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=_self_url(ctx.path, ctx.query),
                status_code=400,
                errors=[ErrorItem(code="VALIDATION_ERROR", message="page must be an integer")],
            )
            return status, env.model_dump(), {}

        if page < 1:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=_self_url(ctx.path, ctx.query),
                status_code=400,
                errors=[ErrorItem(code="VALIDATION_ERROR", message="page must be >= 1")],
            )
            return status, env.model_dump(), {}

        params: dict[str, Any] = {"page": page}
        if q:
            params["search"] = q

        # --- chamada SWAPI ---
        try:
            data = client.get("/films/", params=params)
            results = data.get("results", [])
            items = [attach_id(it) for it in results]

            env = ok(
                data=items,
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=_self_url(ctx.path, {"page": page, "q": q} if q else {"page": page}),
                meta={
                    "page": page,
                    "count": len(items),
                    "total": int(data.get("count", 0)) if str(data.get("count", "0")).isdigit() else None,
                    "page_size": len(items),
                },
            )
            return 200, env.model_dump(), {}

        except SwapiTimeout:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=_self_url(ctx.path, ctx.query),
                status_code=504,
                errors=[ErrorItem(code="UPSTREAM_TIMEOUT", message="SWAPI timeout")],
            )
            return status, env.model_dump(), {}

        except SwapiBadResponse:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=_self_url(ctx.path, ctx.query),
                status_code=502,
                errors=[ErrorItem(code="UPSTREAM_BAD_RESPONSE", message="Invalid response from SWAPI")],
            )
            return status, env.model_dump(), {}

        except SwapiNotFound:
            # raro aqui (lista), mas mantém padrão
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=_self_url(ctx.path, ctx.query),
                status_code=404,
                errors=[ErrorItem(code="UPSTREAM_NOT_FOUND", message="Resource not found on SWAPI")],
            )
            return status, env.model_dump(), {}

        except SwapiUpstreamError:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=_self_url(ctx.path, ctx.query),
                status_code=502,
                errors=[ErrorItem(code="UPSTREAM_ERROR", message="SWAPI error")],
            )
            return status, env.model_dump(), {}
    return handler
