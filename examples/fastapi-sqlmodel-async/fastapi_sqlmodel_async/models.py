from datetime import timezone, datetime
from functools import partial
from uuid import uuid4, UUID

from sqlmodel import SQLModel, Field, Relationship


class Post(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    title: str
    content: str
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))
    published_at: datetime | None = None
    comments: list["Comment"] = Relationship()


class Comment(SQLModel, table=True):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    post_id: UUID = Field(foreign_key="post.id")
    author: str
    message: str
    commented_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))
    post: Post = Relationship(back_populates="comments")
