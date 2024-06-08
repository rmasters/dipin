import warnings
from typing import Callable, Type, TypeVar, TypedDict

T = TypeVar("T")


InstanceType = Type[T]
Instance = T
Factory = Callable[[], T]
Name = str
LookupKey = InstanceType | Name
ContainerKey = tuple[InstanceType, Name | None]


class ContainerItem(TypedDict):
    factory: Instance | Factory
    use_cache: bool


class Container:
    container: dict[ContainerKey, ContainerItem]

    def __init__(self):
        self.container = {}

    def register_instance(
        self,
        instance: Instance,
        type_: InstanceType | None = None,
        name: Name | None = None,
    ):
        if type_ is None:
            type_ = type(instance)

        if name:
            self._check_for_existing_names(name)

        def factory() -> type_:
            return instance

        self.set((type_, name), {"factory": factory, "use_cache": True})

    def register_factory(
        self,
        type_: InstanceType,
        factory: Factory | None = None,
        name: Name | None = None,
        create_once: bool = False,
    ):
        if factory is None:
            if type(type_) is not type:
                raise ValueError(
                    "Omitting a factory function is only supported for classes"
                )
            factory = type_

        if name:
            self._check_for_existing_names(name)

        self.set(
            (type_, name),
            {
                "factory": factory,
                "use_cache": create_once,
            },
        )

    def set(self, key: ContainerKey, item: ContainerItem):
        if key in self.container:
            type_name = ".".join([key[0].__module__, key[0].__qualname__])
            name = f" (named '{key[1]}')" if key[1] else ""
            warnings.warn(
                UserWarning(f"Replacing existing container item {type_name}{name}")
            )

        self.container[key] = item

    def lookup(self, key: LookupKey) -> ContainerKey:
        if isinstance(key, Name):
            type_, name = self._find_by_name(key)
            return type_, name

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

    def get_factory(self, key: ContainerKey) -> Instance | Factory:
        item = self.container[key]
        return item["factory"]

    def should_cache(self, key: ContainerKey) -> bool:
        item = self.container[key]
        return item["use_cache"]

    def __len__(self) -> int:
        return len(self.container)

    def __contains__(self, item: ContainerKey) -> bool:
        return item in self.container

    def __getitem__(self, item: ContainerKey) -> ContainerItem:
        return self.container[item]
