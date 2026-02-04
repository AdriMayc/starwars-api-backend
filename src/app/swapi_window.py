# src/app/swapi_window.py
from __future__ import annotations

from typing import Any

from clients.swapi import SwapiClient, SwapiNotFound

UPSTREAM_PAGE_SIZE = 10  # SWAPI é fixa em 10


def _to_int(v: Any) -> int | None:
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


def fetch_window(
    client: SwapiClient,
    resource: str,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
) -> tuple[list[dict[str, Any]], int | None]:
    """
    Busca apenas as páginas necessárias da SWAPI para atender (page, page_size).
    Retorna (items_slice, total_count).

    Regra importante:
    - SWAPI pode retornar 404 quando 'page' está fora do range (em vez de results=[]).
      Para listagens, isso significa "fim da lista".
    """
    start = (page - 1) * page_size
    end = start + page_size

    up_start = (start // UPSTREAM_PAGE_SIZE) + 1
    up_end = ((end - 1) // UPSTREAM_PAGE_SIZE) + 1

    collected: list[dict[str, Any]] = []
    total: int | None = None

    for up_page in range(up_start, up_end + 1):
        params: dict[str, Any] = {"page": up_page}
        if search:
            params["search"] = search

        try:
            data = client.get(resource, params=params)
        except SwapiNotFound:
            if up_page == up_start:
                raise
            break

        if total is None:
            total = _to_int(data.get("count"))

        results = data.get("results") or []
        collected.extend(results)

        # Se a SWAPI devolver results vazio (raro), também encerra
        if not results:
            break

    offset = start - (up_start - 1) * UPSTREAM_PAGE_SIZE
    window = collected[offset : offset + page_size]
    return window, total
