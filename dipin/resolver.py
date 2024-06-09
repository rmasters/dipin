import inspect
from functools import partial
from typing import get_type_hints, Coroutine, Generator, AsyncGenerator, get_args

import asyncer
from dipin.container import InstanceType, ContainerKey, Factory, Container, Instance, InstanceContainerItem, \
    DefinedFactoryContainerItem, PartialFactoryContainerItem
from dipin.util import is_class_type

DependencyTree = dict[ContainerKey, dict[str, ContainerKey]]


class Resolver:
    container: Container

    def __init__(self, container: Container):
        self.container = container

    def get(self, key: ContainerKey) -> Instance:
        if key not in self.container:
            if not (key := self.autowire(key[0])):
                raise KeyError(f"Unable to resolve {key}")

        item = self.container.get(key)

        if isinstance(item, InstanceContainerItem):
            return item.instance

        assert isinstance(item, (DefinedFactoryContainerItem, PartialFactoryContainerItem))
        factory = self.build_factory_from_factory(item.factory)
        return self.call_factory(factory)

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

    def build_factory_from_class(self, cls: InstanceType) -> Factory:
        ...

    def build_factory_dependencies(self, factory: Factory) -> Factory:
        args = inspect.signature(factory)

        params = {}
        for name, param in args.parameters.items():
            # Attempt to fetch/autowire dependencies
            if param.annotation is not inspect.Parameter.empty:
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

            raise ValueError(f"Unable to fill parameter {name}")

        return partial(factory, **params)

    def autowire(self, type_: InstanceType) -> ContainerKey | None:
        if not self.can_autowire(type_):
            return None

        return self.container.register_factory(type_)

    def can_autowire(self, type_: InstanceType) -> bool:
        return is_class_type(type_)


class ResolverError(RuntimeError): ...


class RequiredDependenciesError(ResolverError):
    def __init__(
        self, dependency: ContainerKey, arguments: list[tuple[str, ContainerKey]]
    ):
        self.dependency = dependency
        self.arguments = arguments

    def __str__(self):
        dep_name = f"{self.dependency[0].__module__}.{self.dependency[0].__qualname__}"
        if self.dependency[1]:
            dep_name += f" (named '{self.dependency[1]}')"
        arg_text = ", ".join(
            [f"{arg_name} ({arg_key[0]})" for arg_name, arg_key in self.arguments]
        )
        return f"Unable to build required dependencies for {dep_name} with unresolved arguments: {arg_text}."


class CircularDependencyError(ResolverError):
    factory: Factory
    argument: str
    container_key: ContainerKey

    def __init__(self, factory: Factory, argument: str, container_key: ContainerKey):
        self.factory = factory
        self.argument = argument
        self.container_key = container_key

    def __str__(self) -> str:
        return f"Cannot construct {self.factory} as {self.argument} ({self.container_key}) has a circular dependency"
