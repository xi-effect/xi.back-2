from typing import Annotated

from pydantic import BaseModel
from tmexio import Emitter, EventException, PydanticPackager

from app.common.abscract_models.ordered_lists_db import InvalidMoveException
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
from app.communities.services import channels_svc
from app.communities.utils.channel_list import (
    ChannelCategoryListItemDict,
    ChannelCategoryListItemSchema,
    build_channels_and_categories_list,
)

router = EventRouterExt(tags=["channels-list"])


@router.on(
    "list-channels",
    summary="List categories and channels in the community",
    dependencies=[current_participant_dependency],
)
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
    summary="Create a new channel in the community",
    server_summary="A new channel has been created in the current community",
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
    duplex_emitter: Annotated[Emitter[Channel], Channel.ServerEventSchema],
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

    channel = await channels_svc.create_channel(
        community_id=community.id,
        category_id=category_id,
        data=data,
    )
    await db.session.commit()

    await duplex_emitter.emit(
        channel,
        target=community_room(channel.community_id),
        exclude_self=True,
    )
    return channel


@router.on(
    "update-channel",
    summary="Update any channel's metadata by id",
    server_summary="Channel's metadata has been updated in the current community",
    dependencies=[current_owner_dependency],
)
async def update_channel(
    channel: ChannelByIds,
    data: Channel.PatchSchema,
    duplex_emitter: Annotated[Emitter[Channel], Channel.ServerEventSchema],
) -> Annotated[Channel, PydanticPackager(Channel.ResponseSchema)]:
    channel.update(**data.model_dump(exclude_defaults=True))
    await db.session.commit()

    await duplex_emitter.emit(
        channel,
        target=community_room(channel.community_id),
        exclude_self=True,
    )
    return channel


class ChannelIdsSchema(BaseModel):
    community_id: int
    channel_id: int


class MoveChannelServerSchema(ChannelIdsSchema):
    category_id: int | None
    after_id: int | None
    before_id: int | None


invalid_mode = EventException(409, "Invalid move")


@router.on(
    "move-channel",
    summary="Update parent category and/or ordering of a channel in a community",
    server_summary="Channel's parent category and/or ordering has been updated in the current community",
    exceptions=[quantity_limit_per_category_exceeded, invalid_mode],
    dependencies=[current_owner_dependency],
)
async def move_channel(
    channel: ChannelByIds,
    category_id: int | None,
    after_id: int | None,
    before_id: int | None,
    duplex_emitter: Emitter[MoveChannelServerSchema],
) -> None:
    if category_id is not None:
        category = await Category.find_first_by_kwargs(
            id=category_id, community_id=channel.community_id
        )
        if category is None:
            raise category_not_found

    if await Channel.is_limit_per_category_reached(  # TODO (33602197) pragma: no cover
        community_id=channel.community_id, category_id=category_id
    ):
        raise quantity_limit_per_category_exceeded
    try:
        await channel.validate_and_move(
            list_id=(channel.community_id, category_id),
            after_id=after_id,
            before_id=before_id,
        )
    except InvalidMoveException as e:  # TODO (33602197) pragma: no cover
        # TODO warns as if the exception is not documented
        raise EventException(409, e.message)

    await db.session.commit()

    await duplex_emitter.emit(
        MoveChannelServerSchema(
            community_id=channel.community_id,
            category_id=channel.category_id,
            channel_id=channel.id,
            after_id=after_id,
            before_id=before_id,
        ),
        target=community_room(channel.community_id),
        exclude_self=True,
    )


@router.on(
    "delete-channel",
    summary="Delete any channel by id",
    server_summary="A channel has been deleted in the current community",
    dependencies=[current_owner_dependency],
)
async def delete_channel(
    channel: ChannelByIds,
    duplex_emitter: Emitter[ChannelIdsSchema],
) -> None:
    await channels_svc.delete_channel(channel)
    await db.session.commit()

    await duplex_emitter.emit(
        ChannelIdsSchema(community_id=channel.community_id, channel_id=channel.id),
        target=community_room(channel.community_id),
        exclude_self=True,
    )
