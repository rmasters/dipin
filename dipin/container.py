import warnings
from dataclasses import dataclass
from typing import Callable, Type, TypeVar

from dipin.util import is_class_type

T = TypeVar("T")


InstanceType = Type[T]
Instance = T
Factory = Callable[[], T]
Name = str
LookupKey = InstanceType | Name
ContainerKey = tuple[InstanceType, Name | None]


@dataclass
class InstanceContainerItem:
    instance: Instance


@dataclass
class PartialFactoryContainerItem:
    use_cache: bool
    factory: Factory


@dataclass
class DefinedFactoryContainerItem:
    use_cache: bool
    factory: Factory


ContainerItem = (
    InstanceContainerItem | PartialFactoryContainerItem | DefinedFactoryContainerItem
)


class Container:
    container: dict[ContainerKey, ContainerItem]
    cache: dict[ContainerKey, Instance]

    def __init__(self):
        self.container = {}
        self.cache = {}

    def register_instance(
        self,
        instance: Instance,
        type_: InstanceType | None = None,
        name: Name | None = None,
    ) -> ContainerKey:
        if type_ is None:
            type_ = type(instance)

        if name:
            self._check_for_existing_names(name)

        self.set((type_, name), InstanceContainerItem(instance=instance))
        return type_, name

    def register_factory(
        self,
        type_: InstanceType,
        factory: Factory | None = None,
        name: Name | None = None,
        create_once: bool = False,
    ) -> ContainerKey:
        if name:
            self._check_for_existing_names(name)

        if factory is None:
            if not is_class_type(type_):
                raise ValueError(
                    "Omitting a factory function is only supported for classes"
                )
            self.set(
                (type_, name),
                PartialFactoryContainerItem(factory=type_, use_cache=create_once),
            )
            return type_, name

        self.set(
            (type_, name),
            DefinedFactoryContainerItem(factory=factory, use_cache=create_once),
        )
        return type_, name

    def set(self, key: ContainerKey, item: ContainerItem):
        if key in self.container:
            type_name = ".".join([key[0].__module__, key[0].__qualname__])
            name = f" (named '{key[1]}')" if key[1] else ""
            warnings.warn(
                UserWarning(f"Replacing existing container item {type_name}{name}")
            )

        self.container[key] = item

    def get(self, key: ContainerKey) -> ContainerItem:
        return self.container[key]

    def lookup(self, key: LookupKey) -> ContainerKey:
        if isinstance(key, Name):
            type_, name = self._find_by_name(key)
            return type_, name

        if (key, None) not in self.container:
            raise KeyError(f"Container item with type {key} not registered")

        return key, None

    def _find_by_name(self, name: str) -> ContainerKey:
        for type_, item_name in self.container.keys():
            if item_name == name:
                return type_, item_name

        raise KeyError(f"Container item with name {name} not registered")

    def _check_for_existing_names(self, name: str):
        try:
            self._find_by_name(name)
        except KeyError:
            # TODO: Handle replacements later
            raise KeyError(f"Existing container item with name {name}")

    def should_cache(self, key: ContainerKey) -> bool:
        item = self.container[key]

        if isinstance(item, InstanceContainerItem):
            return False

        return item.use_cache

    def is_cached(self, key: ContainerKey) -> bool:
        return key in self.cache

    def get_cached(self, key: ContainerKey) -> Instance:
        return self.cache[key]

    def set_cached(self, key: ContainerKey, instance: Instance):
        self.cache[key] = instance

    def __len__(self) -> int:
        return len(self.container)

    def __contains__(self, item: ContainerKey) -> bool:
        return item in self.container

    def __getitem__(self, item: ContainerKey) -> ContainerItem:
        return self.container[item]
