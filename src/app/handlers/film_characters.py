# src/app/handlers/film_characters.py
from __future__ import annotations

from typing import Any

from app.pagination import PaginationError, build_links, build_self_url, parse_pagination
from app.router import RequestContext
from clients.swapi import (
    SwapiBadResponse,
    SwapiClient,
    SwapiNotFound,
    SwapiTimeout,
    SwapiUpstreamError,
)
from clients.utils import attach_id
from schemas.common import ErrorItem, fail, ok


def list_film_characters_handler(client: SwapiClient):
    def handler(ctx: RequestContext):
        film_id = ctx.path_params.get("id")
        q = (ctx.query.get("q") or "").strip() or None

        # 1) paginação
        try:
            page, page_size = parse_pagination(ctx.query)
        except PaginationError as e:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=build_self_url(ctx.path, ctx.query),
                status_code=400,
                errors=[ErrorItem(code="VALIDATION_ERROR", message=str(e))],
            )
            return status, env.model_dump(), {}

        # 2) upstream: buscar filme
        try:
            film = client.get(f"/films/{film_id}/", params=None)
        except SwapiTimeout:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=build_self_url(ctx.path, ctx.query),
                status_code=504,
                errors=[ErrorItem(code="UPSTREAM_TIMEOUT", message="SWAPI timeout")],
            )
            return status, env.model_dump(), {}
        except SwapiBadResponse:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=build_self_url(ctx.path, ctx.query),
                status_code=502,
                errors=[ErrorItem(code="UPSTREAM_BAD_RESPONSE", message="Invalid response from SWAPI")],
            )
            return status, env.model_dump(), {}
        except SwapiNotFound:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=build_self_url(ctx.path, ctx.query),
                status_code=404,
                errors=[ErrorItem(code="UPSTREAM_NOT_FOUND", message="Resource not found on SWAPI")],
            )
            return status, env.model_dump(), {}
        except SwapiUpstreamError:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=build_self_url(ctx.path, ctx.query),
                status_code=502,
                errors=[ErrorItem(code="UPSTREAM_ERROR", message="SWAPI error")],
            )
            return status, env.model_dump(), {}

        # 3) resolver characters URLs
        urls = film.get("characters") or []
        try:
            people: list[dict[str, Any]] = [client.get_by_url(u, params=None) for u in urls]
        except SwapiTimeout:
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=build_self_url(ctx.path, ctx.query),
                status_code=504,
                errors=[ErrorItem(code="UPSTREAM_TIMEOUT", message="SWAPI timeout")],
            )
            return status, env.model_dump(), {}
        except (SwapiBadResponse, SwapiUpstreamError, SwapiNotFound):
            status, env = fail(
                request_id=ctx.headers.get("x-request-id", ""),
                self_url=build_self_url(ctx.path, ctx.query),
                status_code=502,
                errors=[ErrorItem(code="UPSTREAM_BAD_RESPONSE", message="Invalid response from SWAPI")],
            )
            return status, env.model_dump(), {}

        items = [attach_id(it) for it in people]

        # 4) filtro local opcional por q
        if q:
            q_low = q.lower()
            items = [it for it in items if str(it.get("name", "")).lower().find(q_low) >= 0]

        total = len(items)

        # 5) paginação local
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]

        links = build_links(ctx.path, page=page, page_size=page_size, q=q, total=total)

        env = ok(
            data=page_items,
            request_id=ctx.headers.get("x-request-id", ""),
            self_url=links["self"],
            meta={
                "page": page,
                "page_size": page_size,
                "count": len(page_items),
                "total": total,
            },
        )
        payload = env.model_dump()
        payload["links"] = links
        return 200, payload, {}

    return handler
