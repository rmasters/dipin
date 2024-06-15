# dipin

dipin provides a dependency injection container, that primarily aims to work well with FastAPI.

## 🛑 Use [that-depends](https://github.com/modern-python/that-depends) instead

> [!Caution]  
> The inspiration for dipin came from seeing python-dependency-injector was rarely maintained, and wanting better FastAPI integration.
>
> I've since discovered [that-depends](https://github.com/modern-python/that-depends), a successor to PDI that does a **much better** job of dependency management than dipin:
> *   Defined types for singletons, factories, and importantly context-aware factories which I was about to implement
> *   Supports Python 3.12
> *   First-class support for asyncio
> *   Allows defining dependencies in a container class, rather than a module
> *   It doesn't quite do auto-wiring yet (e.g. by prefilling dependency args with dependencies of that type) but wiring it up manually isn't too complex
> *   Is actively maintained, and written in Python so is easy to debug

It's relatively easy to achieve `def handler(dep: DI[Dep])` style injection with that-depends:

```python
# di.py
from typing import Type, Annotated, get_args

from fastapi.params import Depends
from that_depends import BaseContainer
from that_depends.providers import Singleton

from .settings import Settings


T = TypeVar("T")


class FastAPIContainerWrapper:
    container: Type[BaseContainer]

    def __init__(self, container: Type[BaseContainer]):
        self.container = container

    def __getitem__(self, lookup_cls: Type[T]) -> Annotated[Type[T], Depends]:
        container_annotations = getattr(self.container, "__annotations__", {})

        for name, provider in self.container.get_providers().items():
            if name not in container_annotations:
                continue

            if not (annotation := get_args(container_annotations[name])):
                continue

            if (cls := annotation[0]) is lookup_cls:
                return Annotated[cls, Depends(provider)]

        raise ValueError(f"Could not find provider in container for {lookup_cls}")


class Container(BaseContainer):
    settings: Singleton[Settings] = Singleton(Settings)  # <== The type-annotation is used here for lookup


DI = FastAPIContainerWrapper(Container)
```

```python
# app.py

from fastapi import APIRouter
from that_depends.providers.context_resources import DIContextMiddleware

from .di import DI
from .settings import Settings

router = APIRouter(middleware=[DIContextMiddleware])  # type: ignore


@router.get("/")
async def handler(settings: DI[Settings]):
    return {"version": settings.app_version}
```

## Motivation

FastAPI's dependency container works well, but can be messy to scale. Out of
the box, you can end up with many `Annotated[X, Depends()]`. Some projects I've
worked on have a sprawling di.py, and references to Depends in non-FastAPI code.

dipin aims to:
1.  Remove the need to annotate types in non-FastAPI code with `Depends`,
2.  Provide a simple API to access dependencies in route-handlers, e.g.:
    ```python
    from dipin import DI

    @app.get("/")
    async def homepage(request: Request, user: DI[AuthenticatedUser]):
        ...
    ```
    vs
    ```python
    from .auth import get_authenticated_user

    @app.get("/")
    async def homepage(request: Request, user: Annotated[User, Depends(get_authenticated_user)]):
        ...
    ```

## Architecture

TODO

## Usage (alpha, buggy, will change)

```python
# di.py

from dipin import DI

# Register a singleton across all requests
from .settings import Settings  # e.g. a pydantic-settings model
DI.register_instance(Settings())

# Register a factory (lazy singleton), called once across all requests
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

def create_engine(settings: DI[Settings]) -> AsyncEngine:
    return create_async_engine(str(settings.database_dsn))

DI.register_factory(AsyncEngine, get_db_engine, create_once=True)

# Register a factory called per-request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

async def create_session(engine: DI[AsyncEngine]) -> AsyncSession:
    sessionmaker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with sessionmaker() as session:
        yield session

DI.register_factory(AsyncSession, create_session)
```

```python
# app.py

from fastapi import FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession

from dipin import DI

app = FastAPI()

@app.get("/")
async def list_orders(session: DI[AsyncSession]):
    qry = "SELECT * FROM orders"
    res = await session.exec(qry)
    orders = res.all()

    return {"orders": orders}
```

## Roadmap

-   **Support default arguments in factories**
    -   e.g. `class A: def __init__(self, foo: str = "bar")` should be instantiable.
-   **Named dependencies**
    -   e.g. `DI["PrivateOpenAIClient"]`
    -   Out of the box, it seems to lookup the class name (as a deferred annotation), but `typing.Literal` supports this.
-   **Full typing support**
    -   Currently `DI[Class]` does not resolve to an instance of `Class`.
-   **Support many types of dependencies**
    -   Including named (but we won't be able to use `DI[...]`), and some of
        those described in [python-dependency-injector][pdi-providers].
    -   Providing our own `fastapi.Depends` is likely needed.

[pdi-providers]: https://python-dependency-injector.ets-labs.org/providers/index.html
