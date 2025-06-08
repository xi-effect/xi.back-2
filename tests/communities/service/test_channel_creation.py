import json
from collections.abc import Callable
from random import randint
from uuid import uuid4

import pytest
from httpx import Request, Response
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status

from app.common.config import Base, settings
from app.common.schemas.messenger_sch import ChatAccessKind
from app.common.schemas.storage_sch import StorageAccessGroupKind
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.call_channels_db import CallChannel
from app.communities.models.channels_db import Channel, ChannelType
from app.communities.models.chat_channels_db import ChatChannel
from app.communities.models.communities_db import Community
from app.communities.models.task_channels_db import TaskChannel
from app.communities.services import channels_svc
from tests.common.active_session import ActiveSession
from tests.common.respx_ext import assert_last_httpx_request
from tests.communities import factories

pytestmark = pytest.mark.anyio


async def test_post_channel_creation(
    active_session: ActiveSession,
    posts_respx_mock: MockRouter,
    community: Community,
    channel_parent_category_id: int | None,
) -> None:
    channel_raw_data: Channel.InputSchema = factories.ChannelInputFactory.build(
        kind=ChannelType.POSTS
    )

    posts_bridge_mock = posts_respx_mock.post(
        path__regex=r"/post-channels/(?P<channel_id>\d+)/",
    ).respond(status_code=status.HTTP_204_NO_CONTENT)

    async with active_session():
        channel = await channels_svc.create_channel(
            community_id=community.id,
            category_id=channel_parent_category_id,
            data=channel_raw_data,
        )

    assert_contains(
        channel,
        {
            **channel_raw_data.model_dump(),
            "id": int,
            "community_id": community.id,
            "category_id": channel_parent_category_id,
            "list_id": [community.id, channel_parent_category_id],
        },
    )

    assert_last_httpx_request(
        posts_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
        expected_path=f"/internal/post-service/post-channels/{channel.id}/",
        expected_json={"community_id": community.id},
    )


def create_access_group_mock_side_effect_factory(
    access_group_id: str,
) -> Callable[[Request], Response]:
    def create_access_group_mock_side_effect(request: Request) -> Response:
        try:
            json_data = json.loads(request.content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pytest.fail("Invalid request body")

        assert_contains(json_data, {"kind": StorageAccessGroupKind, "related_id": str})
        return Response(
            status_code=status.HTTP_201_CREATED,
            json={
                "id": access_group_id,
                "kind": json_data["kind"],
                "related_id": json_data["related_id"],
            },
        )

    return create_access_group_mock_side_effect


async def test_board_channel_creation(
    active_session: ActiveSession,
    storage_respx_mock: MockRouter,
    community: Community,
    channel_parent_category_id: int | None,
) -> None:
    channel_raw_data: Channel.InputSchema = factories.ChannelInputFactory.build(
        kind=ChannelType.BOARD
    )

    access_group_id = str(uuid4())
    ydoc_id = str(uuid4())

    create_access_group_mock = storage_respx_mock.post(path="/access-groups/").mock(
        side_effect=create_access_group_mock_side_effect_factory(access_group_id)
    )
    create_ydoc_mock = storage_respx_mock.post(
        path=f"/access-groups/{access_group_id}/ydocs/"
    ).respond(status_code=status.HTTP_201_CREATED, json={"id": ydoc_id})

    async with active_session():
        channel = await channels_svc.create_channel(
            community_id=community.id,
            category_id=channel_parent_category_id,
            data=channel_raw_data,
        )

    assert_contains(
        channel,
        {
            **channel_raw_data.model_dump(),
            "id": int,
            "community_id": community.id,
            "category_id": channel_parent_category_id,
            "list_id": [community.id, channel_parent_category_id],
        },
    )

    async with active_session():
        board_channel = await BoardChannel.find_first_by_id(channel.id)
        assert_contains(
            board_channel,
            {"access_group_id": access_group_id, "ydoc_id": ydoc_id},
        )

    assert_last_httpx_request(
        create_access_group_mock,
        expected_headers={"X-Api-Key": settings.api_key},
        expected_json={
            "kind": StorageAccessGroupKind.BOARD_CHANNEL.value,
            "related_id": str(channel.id),
        },
    )
    assert_last_httpx_request(
        create_ydoc_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


def create_chat_mock_side_effect_factory(chat_id: int) -> Callable[[Request], Response]:
    def create_chat_mock_side_effect(request: Request) -> Response:
        try:
            json_data = json.loads(request.content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pytest.fail("Invalid request body")

        assert_contains(json_data, {"access_kind": ChatAccessKind, "related_id": str})
        return Response(
            status_code=status.HTTP_201_CREATED,
            json={
                "id": chat_id,
                "access_kind": json_data["access_kind"],
                "related_id": json_data["related_id"],
            },
        )

    return create_chat_mock_side_effect


async def test_chat_channel_creation(
    active_session: ActiveSession,
    messenger_respx_mock: MockRouter,
    community: Community,
    channel_parent_category_id: int | None,
) -> None:
    channel_raw_data: Channel.InputSchema = factories.ChannelInputFactory.build(
        kind=ChannelType.CHAT
    )

    chat_id = randint(0, 10000)

    create_chat_mock = messenger_respx_mock.post(path="/chats/").mock(
        side_effect=create_chat_mock_side_effect_factory(chat_id)
    )

    async with active_session():
        channel = await channels_svc.create_channel(
            community_id=community.id,
            category_id=channel_parent_category_id,
            data=channel_raw_data,
        )

    assert_contains(
        channel,
        {
            **channel_raw_data.model_dump(),
            "id": int,
            "community_id": community.id,
            "category_id": channel_parent_category_id,
            "list_id": [community.id, channel_parent_category_id],
        },
    )

    async with active_session():
        chat_channel = await ChatChannel.find_first_by_id(channel.id)
        assert_contains(chat_channel, {"chat_id": chat_id})

    assert_last_httpx_request(
        create_chat_mock,
        expected_headers={"X-Api-Key": settings.api_key},
        expected_json={
            "access_kind": ChatAccessKind.CHAT_CHANNEL.value,
            "related_id": str(channel.id),
        },
    )


@pytest.mark.parametrize(
    ("channel_kind", "channel_model"),
    [
        (ChannelType.TASKS, TaskChannel),
        (ChannelType.CALL, CallChannel),
    ],
)
async def test_simple_channel_creation(
    active_session: ActiveSession,
    community: Community,
    channel_parent_category_id: int | None,
    channel_kind: ChannelType,
    channel_model: Base,
) -> None:
    channel_raw_data: Channel.InputSchema = factories.ChannelInputFactory.build(
        kind=channel_kind
    )

    async with active_session():
        channel = await channels_svc.create_channel(
            community_id=community.id,
            category_id=channel_parent_category_id,
            data=channel_raw_data,
        )

    assert_contains(
        channel,
        {
            **channel_raw_data.model_dump(),
            "id": int,
            "community_id": community.id,
            "category_id": channel_parent_category_id,
            "list_id": [community.id, channel_parent_category_id],
        },
    )

    async with active_session():
        specific_channel = await channel_model.find_first_by_id(channel.id)
        assert_contains(specific_channel, {"id": channel.id})
