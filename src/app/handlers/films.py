from __future__ import annotations

from typing import Any

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
from app.pagination import (
    PaginationError,
    parse_pagination,
    build_links,
    build_self_url,
)


def list_films_handler(client: SwapiClient):
    def handler(ctx: RequestContext):
        q = ctx.query.get("q")

        # --- paginação padronizada ---
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

        params: dict[str, Any] = {"page": page}
        if q:
            params["search"] = q

        # --- chamada SWAPI ---
        try:
            data = client.get("/films/", params=params)

            results = data.get("results", [])
            # limitação consciente: SWAPI pagina fixo (~10)
            results = results[:page_size]

            items = [attach_id(it) for it in results]

            total_raw = data.get("count")
            total = (
                int(total_raw)
                if isinstance(total_raw, int)
                or (isinstance(total_raw, str) and total_raw.isdigit())
                else None
            )

            links = build_links(
                ctx.path,
                page=page,
                page_size=page_size,
                q=q,
                total=total,
            )

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

    return handler
