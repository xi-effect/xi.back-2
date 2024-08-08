from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.posts_db import Post


class PostResponses(Responses):
    POST_NOT_FOUND = 404, "Post not found"


@with_responses(PostResponses)
async def get_post_by_id(post_id: Annotated[int, Path()]) -> Post:
    post = await Post.find_first_by_id(post_id)
    if post is None:
        raise PostResponses.POST_NOT_FOUND
    return post


PostById = Annotated[Post, Depends(get_post_by_id)]
