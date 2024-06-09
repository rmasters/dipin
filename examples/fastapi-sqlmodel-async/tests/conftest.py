from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def app() -> TestClient:
    from fastapi_sqlmodel_async.app import app

    return TestClient(app)
