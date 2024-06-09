import asyncio
from uuid import UUID

from dipin import DI
from fastapi import Request, APIRouter, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from ..services import ListPostsService, ReadPostService, WriteCommentService
from ..templates import templates


router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="list_posts")
async def posts_list(request: Request, posts: DI[ListPostsService], page: int = 0):
    posts = await posts.get_posts(page=page)
    return templates.TemplateResponse(request, "posts_list.html", {"posts": posts})


@router.get("/post/{post_id}", response_class=HTMLResponse, name="read_post")
async def read_post(request: Request, posts: DI[ReadPostService], post_id: UUID):
    post, comments = await asyncio.gather(
        posts.get(post_id),
        posts.get_comments(post_id),
    )

    return templates.TemplateResponse(
        request, "posts_detail.html", {"post": post, "comments": comments}
    )


class WriteCommentForm(BaseModel):
    author: str
    comment: str


@router.post(
    "/post/{post_id}/comments", response_class=RedirectResponse, name="write_comment"
)
async def comment_on_post(
    request: Request,
    comments: DI[WriteCommentService],
    post_id: UUID,
    form: WriteCommentForm,
):
    comment = await comments.write_comment(post_id, form.author, form.comment)
    return RedirectResponse(
        request.url_for("read_post").include_query_params(comment_id=comment.id),
        status_code=status.HTTP_303_SEE_OTHER,
    )
