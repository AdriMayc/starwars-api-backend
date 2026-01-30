from app.router import Router


def test_path_param_extraction():
    router = Router()

    def handler(ctx):
        return 200, {"id": ctx.path_params["id"]}, {}

    router.add_route("GET", "/films/{id}", handler)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/films/123",
        query={},
        headers={},
        body=None,
        request_id="rid",
    )

    assert status == 200
    assert payload["id"] == "123"


def test_static_route_has_priority_over_dynamic():
    router = Router()

    def static(ctx):
        return 200, {"route": "static"}, {}

    def dynamic(ctx):
        return 200, {"route": "dynamic"}, {}

    router.add_route("GET", "/films/latest", static)
    router.add_route("GET", "/films/{id}", dynamic)

    status, payload, _ = router.dispatch(
        method="GET",
        path="/films/latest",
        query={},
        headers={},
        body=None,
        request_id="rid",
    )

    assert status == 200
    assert payload["route"] == "static"


def test_method_not_allowed_on_dynamic_route():
    router = Router()

    def handler(ctx):
        return 200, {}, {}

    router.add_route("GET", "/films/{id}", handler)

    status, payload, _ = router.dispatch(
        method="POST",
        path="/films/1",
        query={},
        headers={},
        body=None,
        request_id="rid",
    )

    assert status == 405
    assert payload["errors"][0]["code"] == "METHOD_NOT_ALLOWED"
