from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlencode


class PaginationError(ValueError):
    pass


def parse_int(value: Any, *, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise PaginationError("must be an integer") from e


def parse_pagination(query: Mapping[str, Any]) -> tuple[int, int]:
    page = parse_int(query.get("page"), default=1)
    page_size = parse_int(query.get("page_size"), default=10)

    if page < 1:
        raise PaginationError("page must be >= 1")
    if page_size < 1 or page_size > 50:
        raise PaginationError("page_size must be between 1 and 50")

    return page, page_size


def build_self_url(path: str, query: Mapping[str, Any]) -> str:
    # query order estável: page, page_size, q, demais
    keys = ["page", "page_size", "q"]
    extra = [k for k in query.keys() if k not in keys]
    ordered = keys + sorted(extra)

    # filtra vazios e mantém ordem
    items: list[tuple[str, str]] = []
    for k in ordered:
        if k not in query:
            continue
        v = query.get(k)
        if v is None or v == "":
            continue
        items.append((k, str(v)))

    qs = urlencode(items)
    return f"{path}?{qs}" if qs else path


def build_links(
    path: str,
    *,
    page: int,
    page_size: int,
    q: str | None,
    total: int | None,
) -> dict[str, str | None]:
    base_query: dict[str, Any] = {"page": page, "page_size": page_size}
    if q:
        base_query["q"] = q

    self_url = build_self_url(path, base_query)

    next_url: str | None = None
    prev_url: str | None = None

    if page > 1:
        prev_q = dict(base_query)
        prev_q["page"] = page - 1
        prev_url = build_self_url(path, prev_q)

    if total is not None:
        total_pages = (total + page_size - 1) // page_size
        if page < total_pages:
            next_q = dict(base_query)
            next_q["page"] = page + 1
            next_url = build_self_url(path, next_q)

    return {"self": self_url, "next": next_url, "prev": prev_url}
