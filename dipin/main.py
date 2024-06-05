from fastapi.params import Depends
from typing import Callable, Type, TypeVar, Annotated, TypedDict

T = TypeVar("T")


InstanceType = Type[T]
Instance = T
Factory = Callable[[], T]
Name = str


class ContainerItem(TypedDict):
    factory: Instance | Factory
    use_cache: bool


class Container:
    container: dict[tuple[InstanceType, Name | None], ContainerItem]

    def __init__(self):
        self.container = {}

    def register_instance(
        self,
        instance: Instance,
        type_: InstanceType | None = None,
        name: Name | None = None,
        use_cache: bool = False,
    ):
        if type_ is None:
            type_ = type(instance)

        if name:
            self._check_for_existing_names(name)

        def factory() -> type_:
            return instance

        self.container[(type_, name)] = {
            "factory": factory,
            "use_cache": use_cache,
        }

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

        self.container[(type_, name)] = {
            "factory": factory,
            "use_cache": create_once,
        }

    def _find_by_name(self, name: str) -> tuple[InstanceType, Name]:
        for type_, item_name in self.container.keys():
            if item_name == name:
                return type_, item_name

        raise KeyError(f"Container item with name {name} not registered")

    def _check_for_existing_names(self, name: str):
        try:
            self._find_by_name(name)
        except KeyError:
            # TODO: Replacement handled later
            raise KeyError(f"Existing container item with name {name}")

    def __getitem__(self, key: InstanceType | Name) -> Depends:
        if isinstance(key, Name):
            type_ = self.get_type(key)
            factory, use_cache = self._get(key, inflate_factory=False)
            return Annotated[type_, Depends(factory, use_cache=use_cache)]

        factory, use_cache = self._get(key, inflate_factory=False)
        return Annotated[key, Depends(factory, use_cache=use_cache)]

    def get(self, key: InstanceType | Name) -> Instance | Factory:
        return self._get(key)[0]

    def _get(
        self, key: InstanceType | Name, inflate_factory: bool = True
    ) -> tuple[Instance | Factory, bool]:
        if isinstance(key, Name):
            type_, name = self._find_by_name(key)
            item = self.container[(type_, name)]
        else:
            item = self.container[(key, None)]

        factory = item["factory"]
        use_cache = item["use_cache"]

        if callable(factory) and inflate_factory:
            return factory(), use_cache

        return factory, use_cache

    def get_type(self, key: InstanceType | Name) -> InstanceType:
        if isinstance(key, Name):
            type_, name = self._find_by_name(key)
            return type_

        return key
