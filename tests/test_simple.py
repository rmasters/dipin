from fastapi import FastAPI
from fastapi.testclient import TestClient
from dipin import Container


def test_fastapi_simple_instance_injection():
    DI = Container()

    class Service: ...

    instance = Service()
    DI.register_instance(instance, Service)

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
    DI = Container()

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
    DI = Container()

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
