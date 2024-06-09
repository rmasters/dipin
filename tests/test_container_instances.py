import pytest

from dipin import Container
from dipin.container import InstanceContainerItem


class A: ...


class B: ...


def test_initial_container_size():
    container = Container()

    assert len(container) == 0


def test_register_single_instance():
    container = Container()

    instance = A()
    container.register_instance(instance)

    assert len(container) == 1
    assert (A, None) in container

    item = container[(A, None)]
    assert isinstance(item, InstanceContainerItem)

    assert item.instance is instance


def test_registering_two_types_of_instance():
    container = Container()

    instance_a = A()
    instance_b = B()

    container.register_instance(instance_a)
    container.register_instance(instance_b)

    assert len(container) == 2
    assert (A, None) in container
    assert (B, None) in container

    item_a = container[(A, None)]
    assert isinstance(item_a, InstanceContainerItem)
    assert item_a.instance is instance_a

    item_b = container[(B, None)]
    assert isinstance(item_b, InstanceContainerItem)
    assert item_b.instance is instance_b


def test_registering_two_instances_of_same_type_replaces_instance_and_emits_warning():
    container = Container()

    instance_a = A()
    instance_b = A()

    container.register_instance(instance_a)

    item = container[(A, None)]
    assert item.instance is instance_a

    with pytest.warns() as record:
        container.register_instance(instance_b)

    assert len(record) == 1
    assert (
        str(record[0].message)
        == f"Replacing existing container item {A.__module__}.{A.__qualname__}"
    )

    assert len(container) == 1
    assert (A, None) in container

    item = container[(A, None)]
    assert item.instance is instance_b
