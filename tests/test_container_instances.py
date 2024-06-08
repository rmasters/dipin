import pytest

from dipin import Container


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

    factory_fn = container[(A, None)]["factory"]
    assert callable(factory_fn)
    assert factory_fn() is instance

    assert container[(A, None)]["use_cache"] is True


def test_instance_factory_function_returns_same_instance():
    container = Container()

    instance = A()
    container.register_instance(instance)

    assert container.get_factory((A, None))() is instance
    assert container.get_factory((A, None))() is instance
    assert container.get_factory((A, None))() is instance


def test_registering_two_types_of_instance():
    container = Container()

    instance_a = A()
    instance_b = B()

    container.register_instance(instance_a)
    container.register_instance(instance_b)

    assert len(container) == 2
    assert (A, None) in container
    assert (B, None) in container

    factory_fn_a = container[(A, None)]["factory"]
    assert callable(factory_fn_a)

    factory_fn_b = container[(B, None)]["factory"]
    assert callable(factory_fn_b)

    assert factory_fn_a is not factory_fn_b

    assert factory_fn_a() is instance_a
    assert factory_fn_b() is instance_b

    assert container[(A, None)]["use_cache"] is True
    assert container[(B, None)]["use_cache"] is True


def test_registering_two_instances_of_same_type_replaces_instance_and_emits_warning():
    container = Container()

    instance_a = A()
    instance_b = A()

    container.register_instance(instance_a)

    with pytest.warns() as record:
        container.register_instance(instance_b)

    assert len(record) == 1
    assert (
        str(record[0].message)
        == f"Replacing existing container item {A.__module__}.{A.__qualname__}"
    )

    assert len(container) == 1
    assert (A, None) in container

    factory_fn = container[(A, None)]["factory"]
    assert callable(factory_fn)
    assert factory_fn() is instance_b
