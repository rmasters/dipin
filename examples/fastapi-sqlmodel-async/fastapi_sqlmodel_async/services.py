from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from .repositories import PostRepository, CommentRepository
from .models import Comment, Post


class ListPostsService:
    posts: PostRepository

    def __init__(self, posts: PostRepository):
        self.posts = posts

    async def get_posts(self, page: int = 0) -> list[Post]:
        return await self.posts.get_page(page=page, per_page=5)


class ReadPostService:
    posts: PostRepository
    comments: CommentRepository

    def __init__(self, posts: PostRepository, comments: CommentRepository):
        self.posts = posts
        self.comments = comments

    async def get(self, post_id: UUID) -> Post:
        try:
            return await self.posts.get(post_id)
        except (NoResultFound, MultipleResultsFound):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

    async def get_comments(self, post_id: UUID) -> list[Comment]:
        return await self.comments.get_for_post(post_id)


class WriteCommentService:
    session: AsyncSession
    comments: CommentRepository

    def __init__(self, session: AsyncSession, comments: CommentRepository):
        self.session = session
        self.comments = comments

    async def comment_on_post(
        self, post_id: UUID, author: str, comment: str
    ) -> Comment:
        comment = Comment(
            post_id=post_id,
            author=author,
            message=comment,
        )
        await self.comments.save(comment)
        await self.session.commit()
        return comment
