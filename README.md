# dipin

dipin provides a dependency injection container, that primarily aims to work well with FastAPI.

> [!IMPORTANT]  
> dipin is in very early stages - the API will change, and functionality is surprisingly missing.

## Motivation

FastAPI's dependency container works well, but can be messy to scale. Out of
the box, you can end up with many `Annotated[X, Depends()]`. Some projects I've
worked on have a sprawling di.py, and references to Depends in non-FastAPI code.

dipin aims to:
1.  Remove the need to annotate types in non-FastAPI code with `Depends`,
2.  Provide a simple API to access dependencies in route-handlers, e.g.:
    ```python
    from .di import DI

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

from dipin import Container

DI = Container()

# Register a singleton across all requests
from .settings import Settings  # e.g. a pydantic-settings model
DI.register_instance(Settings(), Settings)

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

from .di import DI

app = FastAPI()

@app.get("/")
async def list_orders(session: DI[AsyncSession]):
    qry = "SELECT * FROM orders"
    res = await session.exec(qry)
    orders = res.all()

    return {"orders": orders}
```

## Roadmap

-   **Autowiring**
    Currently, a factory function is needed for every non-instance dependency.
    -   Some dependencies can be auto-wired, e.g.:  
        ```python
        class Foo: ...
        class Bar:
            def __init__(foo: Foo): ...
        ```
        ```python
        DI.register_factory(Foo)

        # Before
        def create_bar(foo: DI[Foo]): return Bar(foo)
        DI.register_factory(Bar, create_bar)

        # After
        DI.register_factory(Bar)
        ```
    -   It doesn't appear that the current method of creating `params.Depends`
        allows this (you get errors about the Foo dependency not present in the
        query-string). I think the approach is to generate these factory
        functions ourselves.
-   **Support many types of dependencies**
    -   Including named (but we won't be able to use `DI[...]`), and some of
        those described in [python-dependency-injector][pdi-providers].
    -   Providing our own `fastapi.Depends` is likely needed.
-   **Supporting creation of dependencies with decorators**

[pdi-providers]: https://python-dependency-injector.ets-labs.org/providers/index.html
