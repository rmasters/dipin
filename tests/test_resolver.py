import pytest

from dipin.container import Container
from dipin.resolver import Resolver, CircularDependencyError, RequiredDependenciesError


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


def test_resolver_build_requirements():
    container = Container()
    resolver = Resolver(container)

    class A: ...

    class B:
        def __init__(self, a: A): ...

    class C:
        def __init__(self, b: B, a: A): ...

    requirements = resolver.build_required_dependencies((C, None))

    assert len(requirements) == 3

    assert len(requirements[(A, None)]) == 0

    assert len(requirements[(B, None)]) == 1
    assert requirements[(B, None)]["a"] == (A, None)

    assert len(requirements[(C, None)]) == 2
    assert requirements[(C, None)]["b"] == (B, None)
    assert requirements[(C, None)]["a"] == (A, None)


def test_resolver_get_unique_dependencies():
    container = Container()
    resolver = Resolver(container)

    class A: ...

    class B:
        def __init__(self, a: A): ...

    class C:
        def __init__(self, b: B, a: A): ...

    requirements = resolver.build_required_dependencies((C, None))
    unique = resolver.get_unique_dependencies(requirements)

    assert unique == {(A, None), (B, None), (C, None)}


def test_resolver_with_non_type_args():
    container = Container()
    resolver = Resolver(container)

    class A:
        def __init__(self, val: int): ...

    with pytest.raises(RequiredDependenciesError) as e:
        resolver.build_required_dependencies((A, None))

    assert (
        str(e.value)
        == "Unable to build required dependencies for test_resolver.test_resolver_with_non_type_args.<locals>.A with unresolved arguments: val (<class 'int'>)."
    )
