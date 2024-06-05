from typing import Annotated
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient


def test_stock():
    class Service: ...

    class DependentService:
        service: Service

        def __init__(self, service: Annotated[Service, Depends()]):
            self.service = service

    app = FastAPI()

    @app.get("/")
    async def test(svc: Annotated[DependentService, Depends()]):
        return {
            "svc_type": type(svc).__name__,
            "svc_service_type": type(svc.service).__name__,
            "id": id(svc),
        }

    test_client = TestClient(app)
    for _ in range(3):
        resp = test_client.get("/")
        json = resp.json()

        assert json["svc_type"] == "DependentService"
        assert json["svc_service_type"] == "Service"
