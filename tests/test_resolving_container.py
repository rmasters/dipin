from dipin import Container
from dipin.interface import ResolvingContainer
from dipin.resolver import Resolver


def test_resolving_container_caches_create_once_factories():
    class A: ...

    container = Container()
    container.register_factory(A, create_once=True)

    item = container[(A, None)]
    assert item.use_cache is True

    resolver = Resolver(container)
    interface = ResolvingContainer(container, resolver)

    res = interface.retrieve((A, None))
    assert isinstance(res, A)

    res_2 = interface.retrieve((A, None))
    assert res is res_2


def test_resolving_container_doesnt_cache_other_factories():
    class A: ...

    container = Container()
    container.register_factory(A)

    item = container[(A, None)]
    assert item.use_cache is False

    resolver = Resolver(container)
    interface = ResolvingContainer(container, resolver)

    res = interface.retrieve((A, None))
    assert isinstance(res, A)

    res_2 = interface.retrieve((A, None))
    assert res is not res_2
