from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.categories_dep import CategoryById
from app.communities.dependencies.channels_dep import ChannelById
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.models.channels_db import Channel

router = APIRouterExt(tags=["channels mub"])


@router.post(
    "/communities/{community_id}/channels/",
    status_code=201,
    response_model=Channel.ResponseSchema,
    summary="Create a new channel in the default category (append to the end of the list)",
)
async def create_channel(
    community: CommunityById, data: Channel.InputSchema
) -> Channel:
    return await Channel.create(
        community_id=community.id,
        category_id=None,
        **data.model_dump(),
    )


@router.post(
    "/categories/{category_id}/channels/",
    status_code=201,
    response_model=Channel.ResponseSchema,
    summary="Create a new channel in a category (append to the end of the list)",
)
async def create_channel_in_category(
    category: CategoryById, data: Channel.InputSchema
) -> Channel:
    return await Channel.create(
        community_id=category.community_id,
        category_id=category.id,
        **data.model_dump(),
    )


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


@router.delete(
    "/channels/{channel_id}/",
    status_code=204,
    summary="Delete any channel by id",
)
async def delete_channel(channel: ChannelById) -> None:
    await channel.delete()
