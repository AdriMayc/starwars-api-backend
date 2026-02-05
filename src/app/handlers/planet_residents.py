from __future__ import annotations

from typing import Any

from app.concurrency import run_bounded
from app.pagination import PaginationError, build_links, build_self_url, parse_pagination
from app.router import RequestContext
from clients.swapi import (
    RetryConfig,
    SwapiBadResponse,
    SwapiClient,
    SwapiNotFound,
    SwapiTimeout,
    SwapiUpstreamError,
)
from clients.utils import attach_id
from schemas.common import ErrorItem, fail, ok


def list_planet_residents_handler(client: SwapiClient):
    # client "fail-fast" só para o fan-out do correlated endpoint
    client_fast = SwapiClient(
        timeout=2.0,
        retry=RetryConfig(max_retries=0, backoff_base=0.0, backoff_factor=1.0),
    )

    def handler(ctx: RequestContext):
        planet_id = ctx.path_params.get("id")
        q = (ctx.query.get("q") or "").strip() or None

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

        # 1) buscar planeta (1 call) com client normal
        try:
            planet = client.get(f"planets/{planet_id}/", params=None)
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

        urls: list[str] = planet.get("residents") or []
        total = len(urls)

        # 2) pagina ANTES de resolver URLs
        start = (page - 1) * page_size
        end = start + page_size
        page_urls = urls[start:end]

        # 3) fan-out (fail-fast + 1 onda)
        try:
            workers = min(16, max(1, len(page_urls)))
            people: list[dict[str, Any]] = run_bounded(
                lambda u: client_fast.get_by_url(u, params=None),
                page_urls,
                max_workers=workers,
            )
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

        if q:
            q_low = q.lower()
            items = [it for it in items if q_low in str(it.get("name", "")).lower()]

        links = build_links(ctx.path, page=page, page_size=page_size, q=q, total=total)

        env = ok(
            data=items,
            request_id=ctx.headers.get("x-request-id", ""),
            self_url=links["self"],
            meta={
                "page": page,
                "page_size": page_size,
                "count": len(items),
                "total": total,
            },
        )

        payload = env.model_dump()
        payload["links"] = links
        return 200, payload, {}

    return handler
