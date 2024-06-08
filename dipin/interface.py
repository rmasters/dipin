from functools import partial
from typing import Annotated

from dipin.resolver import Resolver
from dipin.container import (
    Instance,
    ContainerKey,
    Container,
    InstanceType,
    Name,
    Factory,
    LookupKey,
)
from fastapi import Depends


class ResolvingContainer:
    """High-level interface for the DI container, using a dependency resolver"""

    container: Container
    resolver: Resolver
    cache: dict[ContainerKey, Instance]

    def __init__(
        self, container: Container | None = None, resolver: Resolver | None = None
    ):
        self.container = container or Container()
        self.resolver = resolver or Resolver(self.container)
        self.cache = {}

    def register_instance(self, instance: Instance, name: str | None = None) -> None:
        type_ = type(instance)

        self.container.register_instance(instance, type_, name)

    def register_factory(
        self,
        type_: InstanceType,
        factory: Factory | None = None,
        name: Name | None = None,
        create_once: bool = False,
    ) -> None:
        self.container.register_factory(type_, factory, name, create_once)

    def get(self, key: LookupKey) -> Instance:
        container_key = self.container.lookup(key)
        return self.retrieve(container_key)

    def __getitem__(self, item: LookupKey) -> Instance:
        return self.get(item)

    def retrieve(self, container_key: ContainerKey) -> Instance:
        should_cache = self.container.should_cache(container_key)

        if should_cache and container_key in self.cache:
            return self.cache[container_key]

        instance = self.resolver.get(container_key)

        if should_cache:
            self.cache[container_key] = instance

        return instance


class FastAPIContainer(ResolvingContainer):
    """High-level interface for the DI container, for FastAPI application"""

    def __getitem__(self, key: LookupKey) -> Depends:
        container_key = self.container.lookup(key)

        return Annotated[
            container_key[0],
            Depends(partial(self.retrieve, container_key), use_cache=False),
        ]
