# src/app/concurrency.py
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable, TypeVar

T = TypeVar("T")


def run_bounded(
    fn: Callable[[str], T],
    items: Iterable[str],
    *,
    max_workers: int = 8,
) -> list[T]:
    """
    Executa fn(item) em paralelo, com limite de threads.
    Mantém a ordem original de 'items' no retorno.
    """
    items_list = list(items)
    if not items_list:
        return []

    results: list[T | None] = [None] * len(items_list)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_map = {ex.submit(fn, url): idx for idx, url in enumerate(items_list)}
        for fut in as_completed(future_map):
            idx = future_map[fut]
            results[idx] = fut.result()

    return [r for r in results if r is not None]
