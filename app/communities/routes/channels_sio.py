from typing import Annotated

from tmexio import AsyncSocket, EventException, PydanticPackager

from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.categories_sio_dep import category_not_found
from app.communities.dependencies.channels_sio_dep import ChannelByIds
from app.communities.dependencies.communities_sio_dep import (
    CommunityById,
    current_owner_dependency,
    current_participant_dependency,
)
from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.rooms import community_room
from app.communities.utils.channel_list import (
    ChannelCategoryListItemDict,
    ChannelCategoryListItemSchema,
    build_channels_and_categories_list,
)

router = EventRouterExt()


@router.on("list-channels", dependencies=[current_participant_dependency])
async def list_channels(
    community: CommunityById,
) -> Annotated[
    list[ChannelCategoryListItemDict],
    PydanticPackager(list[ChannelCategoryListItemSchema]),
]:
    return await build_channels_and_categories_list(community)


quantity_limit_per_community_exceeded = EventException(
    409, "Quantity limit per community exceeded"
)
quantity_limit_per_category_exceeded = EventException(
    409, "Quantity limit per category exceeded"
)


@router.on(
    "create-channel",
    exceptions=[
        category_not_found,
        quantity_limit_per_community_exceeded,
        quantity_limit_per_category_exceeded,
    ],
    dependencies=[current_owner_dependency],
)
async def create_channel(
    community: CommunityById,
    category_id: int | None,
    data: Channel.InputSchema,
    socket: AsyncSocket,
) -> Annotated[Channel, PydanticPackager(Channel.ResponseSchema, code=201)]:
    if category_id is not None:
        category = await Category.find_first_by_kwargs(
            id=category_id, community_id=community.id
        )
        if category is None:
            raise category_not_found

    if await Channel.is_limit_per_community_reached(community_id=community.id):
        raise quantity_limit_per_community_exceeded
    if await Channel.is_limit_per_category_reached(
        community_id=community.id, category_id=category_id
    ):
        raise quantity_limit_per_category_exceeded

    channel = await Channel.create(
        community_id=community.id, category_id=category_id, **data.model_dump()
    )
    await db.session.commit()

    await socket.emit(
        "create-channel",
        {
            "community_id": channel.community_id,
            "category_id": channel.category_id,
            "channel": Channel.ResponseSchema.model_validate(channel).model_dump(
                mode="json"
            ),
        },
        target=community_room(channel.community_id),
        exclude_self=True,
    )
    return channel


@router.on("update-channel", dependencies=[current_owner_dependency])
async def update_channel(
    channel: ChannelByIds,
    data: Channel.PatchSchema,
    socket: AsyncSocket,
) -> Annotated[Channel, PydanticPackager(Channel.ResponseSchema)]:
    channel.update(**data.model_dump(exclude_defaults=True))
    await db.session.commit()

    await socket.emit(
        "update-channel",
        {
            "community_id": channel.community_id,
            "channel": Channel.ResponseSchema.model_validate(channel).model_dump(
                mode="json"
            ),
        },
        target=community_room(channel.community_id),
        exclude_self=True,
    )
    return channel


@router.on("delete-channel", dependencies=[current_owner_dependency])
async def delete_channel(channel: ChannelByIds, socket: AsyncSocket) -> None:
    await channel.delete()
    await db.session.commit()

    await socket.emit(
        "delete-channel",
        {"community_id": channel.community_id, "channel_id": channel.id},
        target=community_room(channel.community_id),
        exclude_self=True,
    )
