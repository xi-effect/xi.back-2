from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import pytest
from freezegun import freeze_time
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.messenger.models.chats_db import Chat
from app.messenger.models.messages_db import Message
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.messenger.factories import MessageInputMUBFactory, MessagePatchFactory

pytestmark = pytest.mark.anyio

MESSAGE_LIST_SIZE = 6


@pytest.fixture()
async def messages_data(
    active_session: ActiveSession,
    chat: Chat,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        messages = [
            await Message.create(
                chat_id=chat.id,
                **MessageInputMUBFactory.build_json(),
            )
            for _ in range(MESSAGE_LIST_SIZE)
        ]
    messages.sort(key=lambda message: message.created_at, reverse=True)

    yield [
        Message.ResponseSchema.model_validate(message, from_attributes=True).model_dump(
            mode="json"
        )
        for message in messages
    ]

    async with active_session():
        for message in messages:
            await message.delete()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, MESSAGE_LIST_SIZE, id="start_to_end"),
        pytest.param(MESSAGE_LIST_SIZE // 2, MESSAGE_LIST_SIZE, id="middle_to_end"),
        pytest.param(0, MESSAGE_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_messages_listing(
    active_session: ActiveSession,
    mub_client: TestClient,
    chat: Chat,
    messages_data: list[AnyJSON],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/messenger-service/chats/{chat.id}/messages/",
            params={"offset": offset, "limit": limit},
        ),
        expected_json=messages_data[offset:limit],
    )


@freeze_time()
async def test_message_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    chat: Chat,
) -> None:
    message_input_data = MessageInputMUBFactory.build_json()
    message_id: int = assert_response(
        mub_client.post(
            f"/mub/messenger-service/chats/{chat.id}/messages/",
            json=message_input_data,
        ),
        expected_code=201,
        expected_json={
            **message_input_data,
            "id": UUID,
            "created_at": datetime_utc_now(),
            "updated_at": None,
        },
    ).json()["id"]

    async with active_session():
        message = await Message.find_first_by_id(message_id)
        assert message is not None
        await message.delete()


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("POST", MessageInputMUBFactory, id="create"),
        pytest.param("GET", None, id="list"),
    ],
)
async def test_chat_not_found(
    mub_client: TestClient,
    active_session: ActiveSession,
    deleted_chat_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/messenger-service/chats/{deleted_chat_id}/messages/",
            params={"offset": 0, "limit": MESSAGE_LIST_SIZE},
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=404,
        expected_json={"detail": "Chat not found"},
    )


async def test_message_retrieving(
    mub_client: TestClient,
    message: Message,
    message_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/messenger-service/messages/{message.id}/"),
        expected_json=message_data,
    )


@freeze_time()
async def test_message_updating(
    mub_client: TestClient,
    message: Message,
    message_data: AnyJSON,
) -> None:
    message_patch_data = MessagePatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/messenger-service/messages/{message.id}/",
            json=message_patch_data,
        ),
        expected_json={
            **message_data,
            **message_patch_data,
            "updated_at": datetime_utc_now(),
        },
    )


async def test_message_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    message: Message,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/messenger-service/messages/{message.id}/"),
    )

    async with active_session():
        assert (await Message.find_first_by_id(message.id)) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", MessagePatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_message_not_finding(
    mub_client: TestClient,
    deleted_message_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/messenger-service/messages/{deleted_message_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=404,
        expected_json={"detail": "Message not found"},
    )
