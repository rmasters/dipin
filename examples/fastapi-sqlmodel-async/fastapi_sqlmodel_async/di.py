from typing import AsyncIterator

from dipin import DI

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from .settings import Settings


DI.register_instance(Settings())


def get_async_engine(settings: DI[Settings]) -> AsyncEngine:
    return create_async_engine(str(settings.db_dsn))


DI.register_factory(AsyncEngine, get_async_engine, create_once=True)


async def create_async_session(engine: DI[AsyncEngine]) -> AsyncIterator[AsyncSession]:
    sessionmaker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with sessionmaker() as session:
        yield session


DI.register_factory(AsyncSession, create_async_session)
