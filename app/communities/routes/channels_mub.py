from typing import Annotated

from fastapi import Body, HTTPException

from app.common.abscract_models.ordered_lists_db import InvalidMoveException
from app.common.config_bdg import posts_bridge
from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.categories_dep import CategoryById
from app.communities.dependencies.channels_dep import ChannelById
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.channels_db import Channel, ChannelType
from app.communities.responses import LimitedListResponses, MoveResponses
from app.communities.utils.channel_list import (
    ChannelCategoryListItemDict,
    ChannelCategoryListItemSchema,
    build_channels_and_categories_list,
)

router = APIRouterExt(tags=["channels mub"])


@router.get(
    "/communities/{community_id}/channels/",
    response_model=list[ChannelCategoryListItemSchema],
    summary="List categories and their channels in the community in user-defined order",
)
async def list_channels_and_categories(
    community: CommunityById,
) -> list[ChannelCategoryListItemDict]:
    return await build_channels_and_categories_list(community)


@router.post(
    "/communities/{community_id}/channels/",
    status_code=201,
    response_model=Channel.ResponseSchema,
    responses=LimitedListResponses.responses(),
    summary="Create a new channel in the default category (append to the end of the list)",
)
async def create_channel(
    community: CommunityById, data: Channel.InputSchema
) -> Channel:
    if await Channel.is_limit_per_community_reached(community_id=community.id):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    if await Channel.is_limit_per_category_reached(
        community_id=community.id, category_id=None
    ):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    channel = await Channel.create(
        community_id=community.id,
        category_id=None,
        **data.model_dump(),
    )
    if channel.kind is ChannelType.POSTS:
        await posts_bridge.create_post_channel(channel.id, channel.community_id)
    elif channel.kind is ChannelType.BOARD:
        await BoardChannel.create(id=channel.id)
    return channel


@router.post(
    "/categories/{category_id}/channels/",
    status_code=201,
    response_model=Channel.ResponseSchema,
    responses=LimitedListResponses.responses(),
    summary="Create a new channel in a category (append to the end of the list)",
)
async def create_channel_in_category(
    category: CategoryById, data: Channel.InputSchema
) -> Channel:
    if await Channel.is_limit_per_community_reached(community_id=category.community_id):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    if await Channel.is_limit_per_category_reached(
        community_id=category.community_id, category_id=category.id
    ):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    channel = await Channel.create(
        community_id=category.community_id,
        category_id=category.id,
        **data.model_dump(),
    )
    if channel.kind is ChannelType.POSTS:
        await posts_bridge.create_post_channel(channel.id, channel.community_id)
    elif channel.kind is ChannelType.BOARD:
        await BoardChannel.create(id=channel.id)
    return channel


@router.put(
    "/communities/{community_id}/channels/positions/",
    status_code=204,
    summary="Reindex channels in the default category",
)
async def reindex_channels(community: CommunityById) -> None:
    await Channel.reindex_by_list_id(list_id=(community.id, None))


@router.put(
    "/categories/{category_id}/channels/positions/",
    status_code=204,
    summary="Reindex channels in a category",
)
async def reindex_channels_in_category(category: CategoryById) -> None:
    await Channel.reindex_by_list_id(list_id=(category.community_id, category.id))


@router.get(
    "/channels/{channel_id}/",
    response_model=Channel.ResponseSchema,
    summary="Retrieve any channel by id",
)
async def retrieve_channel(channel: ChannelById) -> Channel:
    return channel


@router.patch(
    "/channels/{channel_id}/",
    response_model=Channel.ResponseSchema,
    summary="Update any channel by id",
)
async def patch_channel(channel: ChannelById, data: Channel.PatchSchema) -> Channel:
    channel.update(**data.model_dump(exclude_defaults=True))
    return channel


@router.put(
    "/channels/{channel_id}/position/",
    status_code=204,
    responses=LimitedListResponses.responses(MoveResponses.responses()),
    summary="Move channel to a new position",
)
async def move_channel(
    channel: ChannelById,
    category_id: Annotated[int | None, Body()] = None,
    after_id: Annotated[int | None, Body()] = None,
    before_id: Annotated[int | None, Body()] = None,
) -> None:
    if await Channel.is_limit_per_category_reached(
        community_id=channel.community_id, category_id=category_id
    ):  # TODO (33602197) pragma: no cover
        raise LimitedListResponses.QUANTITY_EXCEEDED
    try:
        await channel.validate_and_move(
            list_id=(channel.community_id, category_id),
            after_id=after_id,
            before_id=before_id,
        )
    except InvalidMoveException as e:  # TODO (33602197) pragma: no cover
        raise HTTPException(409, e.message)


@router.delete(
    "/channels/{channel_id}/",
    status_code=204,
    summary="Delete any channel by id",
)
async def delete_channel(channel: ChannelById) -> None:
    if channel.kind is ChannelType.POSTS:
        await posts_bridge.delete_post_channel(channel.id)
    await channel.delete()
