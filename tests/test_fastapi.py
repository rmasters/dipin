from typing import Annotated, get_origin, get_args
from fastapi import FastAPI, Depends, params
from fastapi.testclient import TestClient

from dipin.interface import FastAPIContainer


def test_fastapi_depends_accessor():
    DI = FastAPIContainer()

    class Service: ...

    DI.register_factory(Service)

    dependency = DI[Service]

    origin = get_origin(dependency)
    assert origin is Annotated

    real_type, depends = get_args(dependency)
    assert real_type is Service
    assert isinstance(depends, params.Depends)
    assert depends.use_cache is False

    result = dependency()
    assert isinstance(result, Service)


def test_fastapi_dependency_caching_is_not_used():
    DI = FastAPIContainer()

    class Service: ...

    DI.register_factory(Service, create_once=True)

    dependency = DI[Service]
    _, depends = get_args(dependency)
    assert depends.use_cache is False

    app = FastAPI()

    @app.get("/")
    async def test(svc: DI[Service]) -> int:
        return id(svc)

    test_client = TestClient(app)
    expected_instance_id = id(DI.get(Service))
    for _ in range(3):
        resp = test_client.get("/")
        instance_id = int(resp.text)

        assert instance_id == expected_instance_id


def test_stock_fastapi_experience():
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


def test_di_fastapi_experience():
    DI = FastAPIContainer()

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


def test_fastapi_simple_instance_injection():
    DI = FastAPIContainer()

    class Service: ...

    instance = Service()
    DI.register_instance(instance)

    app = FastAPI()

    @app.get("/")
    async def test(svc: DI[Service]):
        return {
            "type": type(svc).__name__,
            "id": id(svc),
        }

    test_client = TestClient(app)
    for _ in range(3):
        resp = test_client.get("/")
        json = resp.json()

        assert json["type"] == "Service"
        assert json["id"] == id(instance)


def test_fastapi_simple_factory_function_injection():
    DI = FastAPIContainer()

    class Service: ...

    def factory() -> Service:
        return Service()

    DI.register_factory(Service, factory)

    app = FastAPI()

    @app.get("/")
    async def test(svc: DI[Service]):
        return {
            "type": type(svc).__name__,
            "id": id(svc),
        }

    test_client = TestClient(app)
    last_instance_id = None
    for _ in range(3):
        resp = test_client.get("/")
        json = resp.json()

        assert json["type"] == "Service"
        if last_instance_id:
            assert json["id"] != last_instance_id
            last_instance_id = json["id"]


def test_fastapi_simple_factory_class_injection():
    DI = FastAPIContainer()

    class Service: ...

    DI.register_factory(Service)

    app = FastAPI()

    @app.get("/")
    async def test(svc: DI[Service]):
        return {
            "type": type(svc).__name__,
            "id": id(svc),
        }

    test_client = TestClient(app)
    last_instance_id = None
    for _ in range(3):
        resp = test_client.get("/")
        json = resp.json()

        assert json["type"] == "Service"
        if last_instance_id:
            assert json["id"] != last_instance_id
            last_instance_id = json["id"]


def test_fastapi_dependent_services_factory():
    DI = FastAPIContainer()

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


def test_fastapi_dependent_services_resolved():
    DI = FastAPIContainer()

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


def test_fastapi_autowiring():
    DI = FastAPIContainer()

    class Service: ...

    class DependentService:
        service: Service

        def __init__(self, service: Service):
            self.service = service

    app = FastAPI()

    @app.get("/")
    async def test(svc: DI[DependentService]):
        return {
            "svc_type": type(svc).__name__,
            "svc_service_type": type(svc.service).__name__,
            "id": id(svc),
        }

    test_client = TestClient(app)
    resp = test_client.get("/")
    json = resp.json()

    assert json["svc_type"] == "DependentService"
    assert json["svc_service_type"] == "Service"
