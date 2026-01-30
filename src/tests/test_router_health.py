# src/tests/test_router_health.py
from app.main import create_app_router


def test_get_health_ok():
    router = create_app_router()
    status, payload, headers = router.dispatch(
        method="GET",
        path="/health",
        query={},
        headers={},
        body=None,
        request_id="rid-1",
    )

    assert status == 200
    assert payload["data"]["status"] == "ok"
    assert payload["errors"] == []
    assert payload["links"]["self"] == "/health"
    assert "request_id" in payload["meta"]
    assert headers["Content-Type"] == "application/json"


def test_unknown_path_returns_404():
    router = create_app_router()
    status, payload, _headers = router.dispatch(
        method="GET",
        path="/does-not-exist",
        query={},
        headers={},
        body=None,
        request_id="rid-2",
    )

    assert status == 404
    assert payload["data"] is None
    assert payload["errors"][0]["code"] == "NOT_FOUND"


def test_method_not_allowed_returns_405():
    router = create_app_router()
    status, payload, _headers = router.dispatch(
        method="POST",
        path="/health",
        query={},
        headers={},
        body=None,
        request_id="rid-3",
    )

    assert status == 405
    assert payload["errors"][0]["code"] == "METHOD_NOT_ALLOWED"
