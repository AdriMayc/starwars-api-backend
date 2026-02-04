# src/app/swapi_paging.py
from __future__ import annotations

from typing import Any, Mapping

from clients.swapi import SwapiClient

UPSTREAM_PAGE_SIZE = 10  # SWAPI pagina em 10

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
    Retorna itens suficientes do upstream para preencher (page,page_size),
    fazendo múltiplas chamadas SWAPI quando necessário, e devolve total (count).
    """
    start = (page - 1) * page_size
    end = start + page_size

    up_start = (start // UPSTREAM_PAGE_SIZE) + 1
    up_end = ((end - 1) // UPSTREAM_PAGE_SIZE) + 1

    collected: list[dict[str, Any]] = []
    total: int | None = None

    for p in range(up_start, up_end + 1):
        params: dict[str, Any] = {"page": p}
        if search:
            params["search"] = search

        data = client.get(resource, params=params)
        if total is None:
            total = _to_int(data.get("count"))

        results = data.get("results") or []
        collected.extend(results)

        # Se o upstream já não tem mais resultados, não insiste
        if not results:
            break

    # slice local dentro da janela coletada
    offset = start - (up_start - 1) * UPSTREAM_PAGE_SIZE
    window = collected[offset : offset + page_size]
    return window, total
