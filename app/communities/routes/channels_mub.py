from typing import Annotated

from fastapi import Body, HTTPException
from starlette import status

from app.common.abscract_models.ordered_lists_db import InvalidMoveException
from app.common.fastapi_ext import APIRouterExt
from app.common.responses import LimitedListResponses
from app.communities.dependencies.categories_dep import (
    CategoriesResponses,
    ValidatedOptionalCategoryId,
)
from app.communities.dependencies.channels_dep import ChannelById
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.responses import MoveResponses
from app.communities.services import channels_svc
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
    status_code=status.HTTP_201_CREATED,
    response_model=Channel.ResponseSchema,
    responses=LimitedListResponses.responses(),
    summary="Create a new channel in the community (append to the end of the list)",
)
async def create_channel(
    community: CommunityById,
    category_id: ValidatedOptionalCategoryId,
    data: Channel.InputSchema,
) -> Channel:
    if await Channel.is_limit_per_community_reached(community_id=community.id):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    if await Channel.is_limit_per_category_reached(
        community_id=community.id, category_id=category_id
    ):
        raise LimitedListResponses.QUANTITY_EXCEEDED

    return await channels_svc.create_channel(
        community_id=community.id,
        category_id=category_id,
        data=data,
    )


@router.put(
    "/communities/{community_id}/channels/positions/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reindex channels in a community",
)
async def reindex_channels(
    community: CommunityById,
    category_id: ValidatedOptionalCategoryId,
) -> None:
    await Channel.reindex_by_list_id(list_id=(community.id, category_id))


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
    status_code=status.HTTP_204_NO_CONTENT,
    responses=CategoriesResponses.responses(
        LimitedListResponses.responses(MoveResponses.responses())
    ),
    summary="Move channel to a new position",
)
async def move_channel(
    channel: ChannelById,
    category_id: Annotated[int | None, Body()] = None,
    after_id: Annotated[int | None, Body()] = None,
    before_id: Annotated[int | None, Body()] = None,
) -> None:
    if category_id is not None:
        category = await Category.find_first_by_kwargs(
            id=category_id, community_id=channel.community_id
        )
        if category is None:  # TODO (33602197) pragma: no cover
            raise CategoriesResponses.CATEGORY_NOT_FOUND

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
        raise HTTPException(status.HTTP_409_CONFLICT, e.message)


@router.delete(
    "/channels/{channel_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any channel by id",
)
async def delete_channel(channel: ChannelById) -> None:
    await channels_svc.delete_channel(channel=channel)
