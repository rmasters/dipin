from functools import partial
from typing import get_type_hints

from dipin.container import InstanceType, ContainerKey, Factory, Container
from dipin.util import is_class_type

DependencyTree = dict[ContainerKey, dict[str, ContainerKey]]


class Resolver:
    container: Container

    def __init__(self, container: Container):
        self.container = container

    def get(self, key: ContainerKey) -> InstanceType:
        dependencies = self.build_required_dependencies(key)

        factory_deps = {}
        for arg_name, dep in dependencies[key].items():
            factory_deps[arg_name] = self.get(dep)

        factory = self.container.get_factory(key)
        factory = partial(factory, **factory_deps)

        return factory()

    def build_required_dependencies(self, key: ContainerKey) -> DependencyTree:
        """Walk a dependency tree to identify all required dependencies for a given key"""
        requirements: DependencyTree = {key: {}}

        if key in self.container:
            factory = self.container.get_factory(key)
        elif is_class_type(key[0]):
            factory = key[0]
        else:
            raise RequiredDependenciesError(
                f"Unable to build required dependencies for {key} as it has no registered factory function, and is not a class"
            )

        # Identify arguments to the factory function
        factory_args = self.find_factory_args(factory)

        arg_name: str | None = None
        arg_key: ContainerKey | None = None
        unprocessable_args: list[tuple[str, ContainerKey]] = []
        try:
            for arg_name, arg_key in factory_args.items():
                # Identify non-dependency arguments
                # TODO: Pick up default values for arguments
                if not is_class_type(arg_key[0]):
                    unprocessable_args.append((arg_name, arg_key))
                    continue

                requirements[key][arg_name] = arg_key
                # Recurse into this dependency
                requirements.update(self.build_required_dependencies(arg_key))
        except RecursionError as e:
            raise CircularDependencyError(factory, arg_name, arg_key) from e

        if unprocessable_args:
            raise RequiredDependenciesError(key, unprocessable_args)

        return requirements

    def get_unique_dependencies(self, tree: DependencyTree) -> set[ContainerKey]:
        unique = set()
        for key, deps in tree.items():
            unique.add(key)
            for arg_name, dep in deps.items():
                unique.add(dep)
        return unique

    @staticmethod
    def find_factory_args(factory: Factory) -> dict[ContainerKey]:
        # Handle factories that are Object.__init__ types
        if is_class_type(factory):
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
