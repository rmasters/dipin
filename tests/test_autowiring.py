import pytest

from dipin.interface import ResolvingContainer
from dipin.resolver import UnfillableArgumentError


def test_autowiring_of_unregistered_dependencies():
    DI = ResolvingContainer()

    class Service: ...

    assert len(DI) == 0
    assert Service not in DI

    svc = DI.get(Service)
    assert isinstance(svc, Service)

    assert len(DI) == 1
    assert Service in DI


def test_autowiring_of_unregistered_deep_dependencies():
    DI = ResolvingContainer()

    class Service: ...

    class DependentService:
        def __init__(self, svc: Service):
            self.svc = svc

    assert len(DI) == 0
    assert Service not in DI
    assert DependentService not in DI

    svc = DI.get(DependentService)
    assert isinstance(svc, DependentService)

    assert len(DI) == 2
    assert Service in DI
    assert DependentService in DI


def test_autowiring_of_unregistered_dependency_with_non_type_arg():
    DI = ResolvingContainer()

    class Service:
        def __init__(self, api_token: str): ...

    assert len(DI) == 0
    assert Service not in DI

    with pytest.raises(UnfillableArgumentError) as e:
        DI.get(Service)

    assert str(e.value) == "Unable to fill parameter api_token (<class 'str'>)"
