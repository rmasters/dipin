import inspect
from functools import partial
from typing import Generator, AsyncGenerator, get_args, Type

import asyncer
from dipin.container import (
    InstanceType,
    ContainerKey,
    Factory,
    Container,
    Instance,
    InstanceContainerItem,
    DefinedFactoryContainerItem,
    PartialFactoryContainerItem,
)
from dipin.util import is_class_type

DependencyTree = dict[ContainerKey, dict[str, ContainerKey]]


class Resolver:
    container: Container

    def __init__(self, container: Container):
        self.container = container

    def get(self, key: ContainerKey) -> Instance:
        # If the key is not in the container, attempt to autowire it
        if key not in self.container:
            try:
                if not (key_ := self.autowire(key[0])):
                    raise KeyError(f"Unable to resolve {key}")
            except UnfillableArgumentError as e:
                e.dependency = key
                raise e
            key = key_

        item = self.container.get(key)

        if isinstance(item, InstanceContainerItem):
            return item.instance

        try:
            assert isinstance(
                item, (DefinedFactoryContainerItem, PartialFactoryContainerItem)
            )
            factory = self.build_factory_from_factory(item.factory)
            return self.call_factory(factory)
        except RecursionError:
            # TODO: Detect this earlier
            raise CircularDependencyError(key)

    def call_factory(self, factory: Factory) -> Instance:
        if inspect.iscoroutinefunction(factory):
            return asyncer.syncify(factory)()

        result = factory()

        if isinstance(result, AsyncGenerator):

            async def get_next_item(g: AsyncGenerator) -> Instance:
                async for item in g:
                    return item

            return asyncer.syncify(get_next_item)(result)

        if isinstance(result, Generator):
            return next(result)

        return result

    def build_factory_from_factory(self, factory: Factory) -> Factory:
        return self.build_factory_dependencies(factory)

    def build_factory_dependencies(self, factory: Factory) -> Factory:
        args = inspect.signature(factory)

        params = {}
        for name, param in args.parameters.items():
            # Attempt to fetch/autowire dependencies
            if param.annotation is not inspect.Parameter.empty:
                if isinstance(param.annotation, str):
                    raise NotImplementedError(
                        "String annotations are not supported yet"
                    )

                if is_class_type(param.annotation):
                    anno_args = get_args(param.annotation)
                    if len(anno_args) > 0:
                        params[name] = self.get((anno_args[0], None))
                        continue

                    params[name] = self.get((param.annotation, None))
                    continue

            # Use default values
            if param.default is not inspect.Parameter.empty:
                params[name] = param.default
                continue

            raise UnfillableArgumentError(name, param.annotation)

        return partial(factory, **params)

    def autowire(self, type_: InstanceType) -> ContainerKey | None:
        if not self.can_autowire(type_):
            return None

        return self.container.register_factory(type_)

    def can_autowire(self, type_: InstanceType) -> bool:
        return is_class_type(type_)


class ResolverError(RuntimeError): ...


class UnfillableArgumentError(ResolverError):
    arg_name: str
    arg_type: Type
    dependency: ContainerKey | None

    def __init__(
        self, arg_name: str, arg_type: Type, dependency: ContainerKey | None = None
    ):
        self.arg_name = arg_name
        self.arg_type = arg_type
        self.dependency = dependency

    def __str__(self) -> str:
        return f"Unable to fill parameter {self.arg_name} ({self.arg_type})" + (
            " for {self.dependency}" if self.dependency else ""
        )


class CircularDependencyError(ResolverError):
    dependency: ContainerKey

    def __init__(self, dependency: ContainerKey):
        self.dependency = dependency

    def __str__(self) -> str:
        return f"Cannot construct {self.dependency} due to a circular dependency"
