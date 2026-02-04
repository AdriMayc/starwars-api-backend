# src/app/concurrency.py
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from clients.swapi import SwapiClient

def fetch_many_by_url(
    client: SwapiClient,
    urls: list[str],
    *,
    max_workers: int = 10,
) -> list[dict[str, Any]]:
    if not urls:
        return []

    results: list[dict[str, Any]] = [None] * len(urls)  # type: ignore

    def task(i: int, u: str):
        return i, client.get_by_url(u, params=None)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(task, i, u) for i, u in enumerate(urls)]
        for f in as_completed(futures):
            i, payload = f.result()
            results[i] = payload

    return results  # preserve order
