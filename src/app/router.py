# src/app/router.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from schemas.common import ErrorItem, fail


JsonDict = dict[str, Any]
Headers = dict[str, str]
Handler = Callable[["RequestContext"], tuple[int, JsonDict, Headers]]


@dataclass(frozen=True)
class RequestContext:
    method: str
    path: str
    query: Mapping[str, Any]
    headers: Mapping[str, str]
    body: Any


class Router:
    """
    Mini-router mínimo e testável.

    - add_route(method, path, handler)
    - dispatch(method, path, query, headers, body) -> (status, payload, headers)
    """

    def __init__(self) -> None:
        # routes[path][method] = handler
        self._routes: dict[str, dict[str, Handler]] = {}

    # ---------- normalização ----------
    def _norm_method(self, method: str) -> str:
        return (method or "").strip().upper()

    def _norm_path(self, path: str) -> str:
        p = (path or "").strip()
        if not p.startswith("/"):
            p = "/" + p
        if len(p) > 1 and p.endswith("/"):
            p = p[:-1]
        return p

    # ---------- registro ----------
    def add_route(self, method: str, path: str, handler: Handler) -> None:
        m = self._norm_method(method)
        p = self._norm_path(path)
        self._routes.setdefault(p, {})[m] = handler

    # ---------- dispatch ----------
    def dispatch(
        self,
        *,
        method: str,
        path: str,
        query: Mapping[str, Any],
        headers: Mapping[str, str],
        body: Any,
        request_id: str,
    ) -> tuple[int, JsonDict, Headers]:
        m = self._norm_method(method)
        p = self._norm_path(path)

        # Headers padrão (sempre JSON)
        out_headers: Headers = {"Content-Type": "application/json"}

        route_methods = self._routes.get(p)
        if route_methods is None:
            status, env = fail(
                request_id=request_id,
                self_url=p,
                status_code=404,
                errors=[ErrorItem(code="NOT_FOUND", message="Route not found")],
            )
            return status, env.model_dump(), out_headers

        handler = route_methods.get(m)
        if handler is None:
            status, env = fail(
                request_id=request_id,
                self_url=p,
                status_code=405,
                errors=[ErrorItem(code="METHOD_NOT_ALLOWED", message="Method not allowed")],
            )
            return status, env.model_dump(), out_headers

        ctx = RequestContext(method=m, path=p, query=query, headers=headers, body=body)
        status, payload, handler_headers = handler(ctx)

        # força Content-Type JSON e permite headers extras do handler
        merged = {**out_headers, **(handler_headers or {})}
        return status, payload, merged
