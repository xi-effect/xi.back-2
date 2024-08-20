from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.posts.dependencies.post_channels_dep import PostChannelById
from app.posts.dependencies.posts_dep import PostById
from app.posts.models.posts_db import Post

router = APIRouterExt(tags=["posts mub"])


@router.get(
    "/post-channels/{channel_id}/posts/",
    status_code=200,
    response_model=list[Post.ResponseSchema],
    summary="List paginated posts in a channel",
)
async def list_posts(
    channel: PostChannelById,
    offset: int,
    limit: int,
) -> Sequence[Post]:
    return await Post.find_paginated_by_channel_id(channel.id, offset, limit)


@router.post(
    "/post-channels/{channel_id}/posts/",
    status_code=201,
    response_model=Post.ResponseSchema,
    summary="Create a new post in a channel",
)
async def create_post(channel: PostChannelById, data: Post.InputSchema) -> Post:
    return await Post.create(channel_id=channel.id, **data.model_dump())


@router.get(
    "/posts/{post_id}/",
    status_code=200,
    response_model=Post.ResponseSchema,
    summary="Retrieve any post by id",
)
async def retrieve_post(post: PostById) -> Post:
    return post


@router.patch(
    "/posts/{post_id}/",
    status_code=200,
    response_model=Post.ResponseSchema,
    summary="Update any post by id",
)
async def patch_post(post: PostById, data: Post.PatchSchema) -> Post:
    post.update(**data.model_dump(exclude_defaults=True))
    return post


@router.delete(
    "/posts/{post_id}/",
    status_code=204,
    summary="Delete any post by id",
)
async def delete_post(post: PostById) -> None:
    await post.delete()
