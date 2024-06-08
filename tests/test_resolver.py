import pytest

from dipin.container import Container
from dipin.resolver import Resolver, CircularDependencyError


class A:
    def __init__(self): ...


class B:
    def __init__(self, a: A):
        self.a = a


class Circular:
    def __init__(self, c: "Circular"):
        self.c = c


def test_resolver_no_dependencies():
    container = Container()
    container.register_factory(A)

    resolver = Resolver(container)

    a = resolver.get((A, None))
    assert isinstance(a, A)


def test_resolver_single_dependency():
    container = Container()
    container.register_factory(A)
    container.register_factory(B)

    resolver = Resolver(container)

    b = resolver.get((B, None))
    assert isinstance(b, B)
    assert isinstance(b.a, A)


def test_resolver_circular_dependency():
    container = Container()
    container.register_factory(Circular)

    resolver = Resolver(container)

    with pytest.raises(CircularDependencyError):
        resolver.get((Circular, None))
