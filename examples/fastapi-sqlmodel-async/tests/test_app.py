from fastapi.testclient import TestClient


def test_app(app: TestClient):
    resp = app.get("/")
    assert resp.status_code == 200
