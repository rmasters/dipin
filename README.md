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
