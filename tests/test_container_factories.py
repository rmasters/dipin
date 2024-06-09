import pytest

from dipin import Container
from dipin.container import PartialFactoryContainerItem


class A: ...


def test_register_single_factory():
    container = Container()

    container.register_factory(A)

    assert len(container) == 1
    assert (A, None) in container

    item = container.get((A, None))
    assert isinstance(item, PartialFactoryContainerItem)

    factory_fn = item.factory
    assert factory_fn is A
    assert isinstance(factory_fn(), A)

    assert item.use_cache is False


def test_factory_function_returns_different_instances():
    container = Container()

    container.register_factory(A)

    prev_instance_id = 0
    for i in range(3):
        assert id(container[(A, None)].factory()) != prev_instance_id


def test_registering_two_factories_of_same_type_replaces_instance_and_emits_warning():
    class B:
        def __init__(self, val: int):
            self.val = val

    container = Container()

    container.register_factory(B, lambda: B(1))

    with pytest.warns() as record:
        container.register_factory(B, lambda: B(2))

    assert len(record) == 1
    assert (
        str(record[0].message)
        == f"Replacing existing container item {B.__module__}.{B.__qualname__}"
    )

    assert len(container) == 1
    assert (B, None) in container

    factory_fn = container[(B, None)].factory
    assert callable(factory_fn)
    assert factory_fn().val == 2
