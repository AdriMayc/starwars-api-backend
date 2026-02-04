from app.main import main

class DummyReq:
    def __init__(self, method: str, path="/films"):
        self.method = method
        self.path = path
        self.args = {}
        self.headers = {"Origin": "http://localhost:5173"}
    def get_json(self, silent=True):
        return None

def test_options_preflight_returns_204_and_cors_headers():
    resp = main(DummyReq("OPTIONS"))
    assert resp.status_code == 204
    assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert "x-api-key" in resp.headers.get("Access-Control-Allow-Headers", "")
