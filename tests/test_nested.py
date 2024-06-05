from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from dipin import Container


def test_fastapi_dependent_services_factory():
    DI = Container()

    class Service: ...

    DI.register_factory(Service)

    class DependentService:
        service: Service

        def __init__(self, service: Service):
            self.service = service

    DI.register_factory(DependentService, lambda: DependentService(DI.get(Service)))

    app = FastAPI()

    @app.get("/")
    async def test(svc: DI[DependentService]):
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


@pytest.mark.xfail
def test_fastapi_dependent_services_autowiring():
    DI = Container()

    class Service: ...

    DI.register_factory(Service)

    class DependentService:
        service: Service

        def __init__(self, service: DI[Service]):
            self.service = service

    DI.register_factory(DependentService)

    app = FastAPI()

    @app.get("/")
    async def test(svc: DI[DependentService]):
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
