import pytest

from dipin.container import Container
from dipin.resolver import Resolver, CircularDependencyError, UnfillableArgumentError


class A:
    def __init__(self): ...


class B:
    def __init__(self, a: A):
        self.a = a


class Circular:
    def __init__(self, c: "Circular"):
        self.c = c


def test_resolver_simple_factory_dependency():
    container = Container()
    container.register_factory(A)

    resolver = Resolver(container)

    a = resolver.get((A, None))
    assert isinstance(a, A)


def test_resolver_instantiates_dependent():
    container = Container()
    container.register_factory(A)
    container.register_factory(B)

    resolver = Resolver(container)

    b = resolver.get((B, None))
    assert isinstance(b, B)
    assert isinstance(b.a, A)


@pytest.mark.xfail
def test_resolver_circular_dependency():
    container = Container()
    container.register_factory(Circular)

    resolver = Resolver(container)

    with pytest.raises(CircularDependencyError):
        resolver.get((Circular, None))


def test_resolver_fails_on_string_dependencies():
    container = Container()
    container.register_factory(Circular)

    resolver = Resolver(container)

    with pytest.raises(NotImplementedError) as e:
        resolver.get((Circular, None))

    assert str(e.value) == "String annotations are not supported yet"


@pytest.mark.parametrize("use_autowiring", [True, False])
def test_resolver_with_non_type_args(use_autowiring: bool):
    container = Container()
    resolver = Resolver(container)

    class A:
        def __init__(self, val: int): ...

    if not use_autowiring:
        container.register_factory(A)

    with pytest.raises(UnfillableArgumentError) as e:
        resolver.get((A, None))

    assert str(e.value) == "Unable to fill parameter val (<class 'int'>)"


def test_resolver_with_non_type_default_arg():
    container = Container()
    resolver = Resolver(container)

    class A:
        val: int

        def __init__(self, val: int = 1):
            self.val = val

    a = resolver.get((A, None))

    assert isinstance(a, A)
    assert a.val == 1
