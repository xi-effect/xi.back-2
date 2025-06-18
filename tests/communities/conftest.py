from collections.abc import AsyncIterator
from random import randint
from typing import Any
from uuid import uuid4

import pytest
from faker import Faker

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.call_channels_db import CallChannel
from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel, ChannelType
from app.communities.models.chat_channels_db import ChatChannel
from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from app.communities.models.participants_db import Participant
from app.communities.models.task_channels_db import TaskChannel
from app.communities.models.tasks_db import Task
from app.communities.rooms import community_room
from tests.common.active_session import ActiveSession
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.tmexio_testing import (
    TMEXIOListenerFactory,
    TMEXIOTestClient,
    TMEXIOTestServer,
)
from tests.common.types import AnyJSON, PytestRequest
from tests.communities import factories
from tests.factories import ProxyAuthDataFactory


@pytest.fixture()
async def community_data() -> AnyJSON:
    return factories.CommunityFullInputFactory.build_json()


@pytest.fixture()
async def community(
    active_session: ActiveSession,
    community_data: AnyJSON,
) -> Community:
    async with active_session():
        return await Community.create(**community_data)


@pytest.fixture()
async def community_room_listener(
    tmexio_listener_factory: TMEXIOListenerFactory,
    community: Community,
) -> TMEXIOTestClient:
    return await tmexio_listener_factory(community_room(community.id))


@pytest.fixture()
async def deleted_community_id(
    active_session: ActiveSession,
    community: Community,
) -> int:
    async with active_session():
        await community.delete()
    return community.id


@pytest.fixture()
def owner_proxy_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def owner_user_id(owner_proxy_auth_data: ProxyAuthData) -> int:
    return owner_proxy_auth_data.user_id


@pytest.fixture()
async def owner(
    active_session: ActiveSession,
    community: Community,
    owner_user_id: int,
) -> Participant:
    async with active_session():
        return await Participant.create(
            community_id=community.id,
            user_id=owner_user_id,
            is_owner=True,
        )


@pytest.fixture()
def owner_data(owner: Participant) -> AnyJSON:
    return Participant.MUBResponseSchema.model_validate(
        owner, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def tmexio_owner_client(
    tmexio_server: TMEXIOTestServer,
    owner_proxy_auth_data: ProxyAuthData,
    owner: Participant,
) -> AsyncIterator[TMEXIOTestClient]:
    async with tmexio_server.authorized_client(owner_proxy_auth_data) as client:
        yield client


@pytest.fixture()
def participant_proxy_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def participant_user_id(participant_proxy_auth_data: ProxyAuthData) -> int:
    return participant_proxy_auth_data.user_id


@pytest.fixture()
async def participant(
    active_session: ActiveSession,
    community: Community,
    participant_user_id: int,
) -> Participant:
    async with active_session():
        return await Participant.create(
            community_id=community.id,
            user_id=participant_user_id,
        )


@pytest.fixture()
def participant_data(participant: Participant) -> AnyJSON:
    return Participant.MUBResponseSchema.model_validate(
        participant, from_attributes=True
    ).model_dump(mode="json")


PARTICIPANT_LIST_SIZE = 6


@pytest.fixture()
async def participants_data(
    active_session: ActiveSession,
    community: Community,
    participant_user_id: int,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        participants = [
            await Participant.create(
                community_id=community.id,
                user_id=participant_user_id,
            )
            for _ in range(PARTICIPANT_LIST_SIZE)
        ]
    participants.sort(key=lambda participant: participant.created_at, reverse=True)

    yield [
        Participant.MUBResponseSchema.model_validate(
            participant, from_attributes=True
        ).model_dump(mode="json")
        for participant in participants
    ]

    async with active_session():
        for participant in participants:
            await participant.delete()


@pytest.fixture()
async def tmexio_participant_client(
    tmexio_server: TMEXIOTestServer,
    participant_proxy_auth_data: ProxyAuthData,
    participant: Participant,
) -> AsyncIterator[TMEXIOTestClient]:
    async with tmexio_server.authorized_client(participant_proxy_auth_data) as client:
        yield client


@pytest.fixture()
async def deleted_participant_id(
    active_session: ActiveSession,
    participant: Participant,
) -> int:
    async with active_session():
        await participant.delete()
    return participant.id


@pytest.fixture(
    params=[pytest.param(True, id="owner"), pytest.param(False, id="participant")]
)
def actor_is_owner(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.fixture()
def actor_user_id(
    owner: Participant, participant: Participant, actor_is_owner: bool
) -> int:
    return owner.user_id if actor_is_owner else participant.user_id


@pytest.fixture()
def tmexio_actor_client(
    tmexio_owner_client: TMEXIOTestClient,
    tmexio_participant_client: TMEXIOTestClient,
    actor_is_owner: bool,
) -> TMEXIOTestClient:
    return tmexio_owner_client if actor_is_owner else tmexio_participant_client


@pytest.fixture()
def outsider_proxy_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_user_id(outsider_proxy_auth_data: ProxyAuthData) -> int:
    return outsider_proxy_auth_data.user_id


@pytest.fixture()
async def tmexio_outsider_client(
    tmexio_server: TMEXIOTestServer,
    outsider_proxy_auth_data: ProxyAuthData,
) -> AsyncIterator[TMEXIOTestClient]:
    async with tmexio_server.authorized_client(outsider_proxy_auth_data) as client:
        yield client


@pytest.fixture()
async def invitation(
    active_session: ActiveSession,
    community: Community,
) -> Invitation:
    async with active_session():
        return await Invitation.create(
            community_id=community.id,
            **factories.InvitationMUBInputFactory.build_json(),
        )


@pytest.fixture(
    params=[
        pytest.param(factories.ExpiredInvitationDataFactory, id="expired"),
        pytest.param(factories.OverusedInvitationDataFactory, id="overused"),
    ]
)
async def invalid_invitation(
    active_session: ActiveSession,
    community: Community,
    request: PytestRequest[type[BaseModelFactory[Any]]],
) -> Invitation:
    async with active_session():
        return await Invitation.create(
            community_id=community.id,
            **request.param.build_json(),
        )


@pytest.fixture()
def invitation_data(invitation: Invitation) -> AnyJSON:
    return Invitation.ResponseSchema.model_validate(
        invitation, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_invitation(
    active_session: ActiveSession,
    invitation: Invitation,
) -> Invitation:
    async with active_session():
        await invitation.delete()
    return invitation


@pytest.fixture()
async def deleted_invitation_id(deleted_invitation: Invitation) -> int:
    return deleted_invitation.id


@pytest.fixture()
async def deleted_invitation_code(deleted_invitation: Invitation) -> str:
    return deleted_invitation.token


INVITATION_LIST_SIZE = 6


@pytest.fixture()
async def invitations_data(
    active_session: ActiveSession,
    community: Community,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        invitations = [
            await Invitation.create(
                community_id=community.id,
                **factories.InvitationMUBInputFactory.build_json(),
            )
            for _ in range(INVITATION_LIST_SIZE)
        ]
    invitations.sort(key=lambda invitation: invitation.created_at)

    yield [
        Invitation.ResponseSchema.model_validate(
            invitation, from_attributes=True
        ).model_dump(mode="json")
        for invitation in invitations
    ]

    async with active_session():
        for invitation in invitations:
            await invitation.delete()


@pytest.fixture()
async def category_data() -> AnyJSON:
    return factories.CategoryInputFactory.build_json()


@pytest.fixture()
async def category(
    active_session: ActiveSession,
    community: Community,
    category_data: AnyJSON,
) -> Category:
    async with active_session():
        return await Category.create(community_id=community.id, **category_data)


@pytest.fixture()
async def deleted_category_id(
    active_session: ActiveSession,
    category: Category,
) -> int:
    async with active_session():
        await category.delete()
    return category.id


CATEGORY_LIST_SIZE = 5


@pytest.fixture()
async def categories_data(
    active_session: ActiveSession,
    community: Community,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        categories = [
            await Category.create(
                community_id=community.id,
                **factories.CategoryInputFactory.build_json(),
            )
            for _ in range(CATEGORY_LIST_SIZE)
        ]
    categories.sort(key=lambda category: category.position)

    yield [
        Category.ResponseSchema.model_validate(
            category, from_attributes=True
        ).model_dump(mode="json")
        for category in categories
    ]

    async with active_session():
        for category in categories:
            await category.delete()


@pytest.fixture()
async def channel_raw_data() -> Channel.InputSchema:
    return factories.ChannelInputFactory.build()


@pytest.fixture()
async def channel_data(channel_raw_data: Channel.InputSchema) -> AnyJSON:
    return channel_raw_data.model_dump(mode="json")


@pytest.fixture()
async def channel(
    active_session: ActiveSession,
    community: Community,
    channel_raw_data: Channel.InputSchema,
) -> Channel:
    async with active_session():
        return await Channel.create(
            community_id=community.id, **channel_raw_data.model_dump()
        )


@pytest.fixture(
    params=[
        pytest.param(channel_kind, id=channel_kind.value)
        for channel_kind in ChannelType
    ]
)
async def specific_channel_kind(request: PytestRequest[ChannelType]) -> ChannelType:
    return request.param


@pytest.fixture()
async def specific_channel_data(specific_channel_kind: ChannelType) -> AnyJSON:
    return factories.ChannelInputFactory.build_json(kind=specific_channel_kind)


@pytest.fixture()
async def specific_channel(
    active_session: ActiveSession,
    community: Community,
    specific_channel_data: AnyJSON,
) -> Channel:
    async with active_session():
        return await Channel.create(community_id=community.id, **specific_channel_data)


CHANNEL_LIST_SIZE = 5


@pytest.fixture()
async def channels_without_category_data(
    active_session: ActiveSession,
    community: Community,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        channels = [
            await Channel.create(
                community_id=community.id,
                **factories.ChannelInputFactory.build_json(),
            )
            for _ in range(CHANNEL_LIST_SIZE)
        ]
    channels.sort(key=lambda channel: channel.position)

    yield [
        Channel.ResponseSchema.model_validate(channel, from_attributes=True).model_dump(
            mode="json"
        )
        for channel in channels
    ]

    async with active_session():
        for channel in channels:
            await channel.delete()


@pytest.fixture()
async def channels_with_category_data(
    active_session: ActiveSession,
    community: Community,
    category: Category,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        channels = [
            await Channel.create(
                community_id=community.id,
                category_id=category.id,
                **factories.ChannelInputFactory.build_json(),
            )
            for _ in range(CHANNEL_LIST_SIZE)
        ]
    channels.sort(key=lambda channel: channel.position)

    yield [
        Channel.ResponseSchema.model_validate(channel, from_attributes=True).model_dump(
            mode="json"
        )
        for channel in channels
    ]

    async with active_session():
        for channel in channels:
            await channel.delete()


@pytest.fixture()
async def deleted_channel_id(
    active_session: ActiveSession,
    channel: Channel,
) -> int:
    async with active_session():
        await channel.delete()
    return channel.id


@pytest.fixture(params=[False, True], ids=["without_category", "with_category"])
def channel_parent_category_id(
    request: PytestRequest[bool], category: Category
) -> int | None:
    return category.id if request.param else None


@pytest.fixture()
async def board_channel(
    faker: Faker, active_session: ActiveSession, channel: Channel
) -> BoardChannel:
    async with active_session():
        return await BoardChannel.create(
            id=channel.id,
            access_group_id=str(uuid4()),
            ydoc_id=str(uuid4()),
        )


@pytest.fixture()
async def board_channel_data(board_channel: BoardChannel) -> AnyJSON:
    return BoardChannel.ResponseSchema.model_validate(
        board_channel, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_board_channel_id(
    active_session: ActiveSession, board_channel: BoardChannel
) -> int:
    async with active_session():
        await board_channel.delete()
    return board_channel.id


@pytest.fixture()
async def chat_channel(active_session: ActiveSession, channel: Channel) -> ChatChannel:
    async with active_session():
        return await ChatChannel.create(
            id=channel.id,
            chat_id=randint(0, 10000),
        )


@pytest.fixture()
async def deleted_chat_channel_id(
    active_session: ActiveSession, chat_channel: BoardChannel
) -> int:
    async with active_session():
        await chat_channel.delete()
    return chat_channel.id


@pytest.fixture()
async def task_channel(active_session: ActiveSession, channel: Channel) -> TaskChannel:
    async with active_session():
        return await TaskChannel.create(id=channel.id)


@pytest.fixture()
async def deleted_task_channel_id(
    active_session: ActiveSession,
    task_channel: TaskChannel,
) -> int:
    async with active_session():
        await task_channel.delete()
    return task_channel.id


@pytest.fixture()
async def task(
    active_session: ActiveSession,
    task_channel: TaskChannel,
) -> Task:
    async with active_session():
        return await Task.create(
            channel_id=task_channel.id,
            **factories.TaskInputFactory.build_json(),
        )


@pytest.fixture()
def task_data(task: Task) -> AnyJSON:
    return Task.ResponseSchema.model_validate(task, from_attributes=True).model_dump(
        mode="json"
    )


@pytest.fixture()
async def deleted_task_id(
    active_session: ActiveSession,
    task: Task,
) -> int:
    async with active_session():
        await task.delete()
    return task.id


@pytest.fixture()
async def call_channel(active_session: ActiveSession, channel: Channel) -> CallChannel:
    async with active_session():
        return await CallChannel.create(id=channel.id)


@pytest.fixture()
async def deleted_call_channel_id(
    active_session: ActiveSession, call_channel: CallChannel
) -> int:
    async with active_session():
        await call_channel.delete()
    return call_channel.id
