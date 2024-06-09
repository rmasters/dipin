from typing import TypeVar, Generic
from uuid import UUID

from sqlalchemy import desc
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select
from .models import Post, Comment

Model = TypeVar("Model", bound=SQLModel)


class SQLModelRepository(Generic[Model]):
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, pk: UUID) -> Model:
        return (await self.session.get(Model, pk)).one()

    async def save(self, model: Model) -> Model:
        self.session.add(model)
        return model


class PostRepository(SQLModelRepository[Post]):
    async def get_page(self, page: int = 0, per_page: int = 5) -> list[Post]:
        qry = (
            select(Post)
            .where(Post.published_at != None)  # noqa
            .order_by(desc(Post.published_at))
            .offset(page * per_page)
            .limit(per_page)
        )
        return (await self.session.exec(qry)).all()


class CommentRepository(SQLModelRepository[Comment]):
    async def get_for_post(self, post_id: UUID) -> list[Comment]:
        qry = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(desc(Comment.commented_at))
        )
        return (await self.session.exec(qry)).all()
