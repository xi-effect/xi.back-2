from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Annotated, TypedDict

from fastapi import Body, HTTPException
from pydantic import BaseModel

from app.common.abscract_models.ordered_lists_db import InvalidMoveException
from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.categories_dep import CategoryById
from app.communities.dependencies.channels_dep import ChannelById
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.responses import LimitedListResponses, MoveResponses

router = APIRouterExt(tags=["channels mub"])


class ChannelCategoryListItemSchema(BaseModel):
    category: Category.ResponseSchema | None
    channels: list[Channel.ResponseSchema]


class ChannelCategoryListItemDict(TypedDict):
    category: Category | None
    channels: list[Channel]


def collect_channels_and_categories_list(
    categories: Sequence[Category],
    category_id_to_channels: dict[None | int, list[Channel]],
) -> Iterable[ChannelCategoryListItemDict]:
    yield {
        "category": None,
        "channels": category_id_to_channels[None],
    }
    for category in categories:  # noqa: WPS526  # yield from messes with mypy
        yield {
            "category": category,
            "channels": category_id_to_channels[category.id],
        }


@router.get(
    "/communities/{community_id}/channels/",
    response_model=list[ChannelCategoryListItemSchema],
    summary="List categories and their channels in the community in user-defined order",
)
async def list_channels_and_categories(
    community: CommunityById,
) -> list[ChannelCategoryListItemDict]:
    categories = await Category.find_all_by_community_id(community_id=community.id)
    channels = await Channel.find_all_by_community_id(community_id=community.id)

    category_id_to_channels: dict[None | int, list[Channel]] = defaultdict(list)
    for channel in channels:
        category_id_to_channels[channel.category_id].append(channel)

    return list(
        collect_channels_and_categories_list(categories, category_id_to_channels)
    )


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
    return await Channel.create(
        community_id=community.id,
        category_id=None,
        **data.model_dump(),
    )


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
    return await Channel.create(
        community_id=category.community_id,
        category_id=category.id,
        **data.model_dump(),
    )


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
    ):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    try:
        await channel.validate_and_move(
            list_id=(channel.community_id, category_id),
            after_id=after_id,
            before_id=before_id,
        )
    except InvalidMoveException as e:
        raise HTTPException(409, e.message)


@router.delete(
    "/channels/{channel_id}/",
    status_code=204,
    summary="Delete any channel by id",
)
async def delete_channel(channel: ChannelById) -> None:
    await channel.delete()
