from functools import partial
from typing import get_type_hints

from dipin.container import InstanceType, ContainerKey, Factory, Container


class Resolver:
    container: Container

    def __init__(self, container: Container):
        self.container = container

    def get(self, key: ContainerKey) -> InstanceType:
        factory = self.container.get_factory(key)

        # Identify arguments to the factory function
        factory_args = self.find_factory_args(factory)

        resolved_args: dict[InstanceType] = {}
        arg_name: str | None = None
        arg_key: ContainerKey | None = None
        try:
            for arg_name, arg_key in factory_args.items():
                resolved_args[arg_name] = self.get(arg_key)
        except RecursionError as e:
            raise CircularDependencyError(factory, arg_name, arg_key) from e

        # Populate known args
        factory = partial(factory, **resolved_args)

        return factory()

    @staticmethod
    def find_factory_args(factory: Factory) -> dict[ContainerKey]:
        # Handle factories that are Object.__init__ types
        if type(factory) is type:
            factory = getattr(factory, "__init__", None)
            if factory is None:
                raise Exception(
                    f"Type {factory} does not define an __init__ method to introspect"
                )

        matches = {}

        args = get_type_hints(factory)
        args.pop("return", None)

        for name, type_ in args.items():
            matches[name] = (type_, None)

        return matches


class CircularDependencyError(Exception):
    factory: Factory
    argument: str
    container_key: ContainerKey

    def __init__(self, factory: Factory, argument: str, container_key: ContainerKey):
        self.factory = factory
        self.argument = argument
        self.container_key = container_key

    def __str__(self) -> str:
        return f"Cannot construct {self.factory} as {self.argument} ({self.container_key}) has a circular dependency"
