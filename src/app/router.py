from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from schemas.common import ErrorItem, fail

JsonDict = dict[str, Any]
Headers = dict[str, str]
Handler = Callable[["RequestContext"], tuple[int, JsonDict, Headers]]

_PARAM_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass(frozen=True)
class RequestContext:
    method: str
    path: str
    query: Mapping[str, Any]
    headers: Mapping[str, str]
    body: Any
    path_params: Mapping[str, str]


@dataclass(frozen=True)
class Route:
    template: str
    pattern: re.Pattern[str]
    param_names: tuple[str, ...]
    methods: dict[str, Handler]


def _compile_template(template: str) -> tuple[re.Pattern[str], tuple[str, ...]]:
    """
    Converte '/films/{id}/characters' em regex com grupos nomeados.
    """
    names: list[str] = []

    def repl(m: re.Match[str]) -> str:
        name = m.group(1)
        names.append(name)
        return fr"(?P<{name}>[^/]+)"

    escaped = re.escape(template)
    # re.escape transforma '{' e '}' em '\{' '\}', então substituímos a versão escapada.
    # Ex.: '/films/\{id\}' -> '/films/(?P<id>[^/]+)'
    escaped = re.sub(r"\\\{([a-zA-Z_][a-zA-Z0-9_]*)\\\}", repl, escaped)
    pattern = re.compile(rf"^{escaped}$")
    return pattern, tuple(names)


class Router:
    """
    Mini-router testável.
    - Suporta rotas estáticas e templates com path params.
    - Retorna (status, payload_dict, headers_dict).
    """

    def __init__(self) -> None:
        self._static: dict[str, dict[str, Handler]] = {}
        self._dynamic: list[Route] = []

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

        if _PARAM_RE.search(p) is None:
            self._static.setdefault(p, {})[m] = handler
            return

        pattern, names = _compile_template(p)

        # Reusa rota se mesmo template já existe
        for r in self._dynamic:
            if r.template == p:
                r.methods[m] = handler
                return

        self._dynamic.append(
            Route(template=p, pattern=pattern, param_names=names, methods={m: handler})
        )

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

        out_headers: Headers = {"Content-Type": "application/json"}

        # 1) match estático
        methods = self._static.get(p)
        if methods is not None:
            handler = methods.get(m)
            if handler is None:
                status, env = fail(
                    request_id=request_id,
                    self_url=p,
                    status_code=405,
                    errors=[ErrorItem(code="METHOD_NOT_ALLOWED", message="Method not allowed")],
                )
                return status, env.model_dump(), out_headers

            ctx = RequestContext(
                method=m,
                path=p,
                query=query,
                headers=headers,
                body=body,
                path_params={},
            )
            status, payload, handler_headers = handler(ctx)
            return status, payload, {**out_headers, **(handler_headers or {})}

        # 2) match dinâmico
        matched_route: Route | None = None
        matched_params: dict[str, str] | None = None

        for r in self._dynamic:
            mm = r.pattern.match(p)
            if mm:
                matched_route = r
                matched_params = mm.groupdict()
                break

        if matched_route is None:
            status, env = fail(
                request_id=request_id,
                self_url=p,
                status_code=404,
                errors=[ErrorItem(code="NOT_FOUND", message="Route not found")],
            )
            return status, env.model_dump(), out_headers

        handler = matched_route.methods.get(m)
        if handler is None:
            status, env = fail(
                request_id=request_id,
                self_url=p,
                status_code=405,
                errors=[ErrorItem(code="METHOD_NOT_ALLOWED", message="Method not allowed")],
            )
            return status, env.model_dump(), out_headers

        ctx = RequestContext(
            method=m,
            path=p,
            query=query,
            headers=headers,
            body=body,
            path_params=matched_params or {},
        )
        status, payload, handler_headers = handler(ctx)
        return status, payload, {**out_headers, **(handler_headers or {})}
