# src/app/main.py
from __future__ import annotations

import uuid
from typing import Any

from flask import jsonify, Request, Response  # ✅ trocou make_response por Response

from app.router import Router, RequestContext
from clients.swapi import SwapiClient
from app.handlers.films import list_films_handler
from app.handlers.people import list_people_handler
from app.handlers.planets import list_planets_handler
from app.handlers.starships import list_starships_handler
from app.handlers.film_characters import list_film_characters_handler
from app.handlers.planet_residents import list_planet_residents_handler
from schemas.common import ok


def _new_request_id() -> str:
    return str(uuid.uuid4())


def health_handler(ctx: RequestContext) -> tuple[int, dict[str, Any], dict[str, str]]:
    env = ok(
        data={"status": "ok"},
        request_id=ctx.headers.get("x-request-id") or _new_request_id(),
        self_url=ctx.path,
    )
    return 200, env.model_dump(), {}


def create_app_router(swapi_client: SwapiClient | None = None) -> Router:
    router = Router()
    router.add_route("GET", "/health", health_handler)

    client = swapi_client or SwapiClient(sleep_fn=lambda _: None)
    router.add_route("GET", "/films", list_films_handler(client))
    router.add_route("GET", "/people", list_people_handler(client))
    router.add_route("GET", "/planets", list_planets_handler(client))
    router.add_route("GET", "/starships", list_starships_handler(client))
    router.add_route("GET", "/films/{id}/characters", list_film_characters_handler(client))
    router.add_route("GET", "/planets/{id}/residents", list_planet_residents_handler(client))
    return router


# --- CORS ---
def _cors_headers(origin: str | None) -> dict[str, str]:
    """
    CORS em dev: ecoa o Origin quando existe.
    - resolve localhost vs 127.0.0.1
    - mantém compatível com browser (preflight)
    """
    allow_origin = origin or "*"  # se não vier Origin (curl), libera geral

    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Vary": "Origin",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "accept,content-type,x-api-key,x-request-id",
        "Access-Control-Max-Age": "3600",
    }


def main(request: Request):
    origin = request.headers.get("Origin")

    # Preflight CORS
    if request.method == "OPTIONS":
        resp = Response(status=204)  # ✅ não precisa de app context
        for k, v in _cors_headers(origin).items():
            resp.headers[k] = v
        return resp

    router = create_app_router()

    request_id = request.headers.get("x-request-id") or _new_request_id()
    status, payload, headers = router.dispatch(
        method=request.method,
        path=request.path,
        query=request.args.to_dict(flat=True),
        headers=dict(request.headers),
        body=request.get_json(silent=True),
        request_id=request_id,
    )

    resp = jsonify(payload)
    resp.status_code = status

    # headers do handler + CORS
    merged = dict(headers or {})
    merged.update(_cors_headers(origin))
    for k, v in merged.items():
        resp.headers[k] = v

    return resp
