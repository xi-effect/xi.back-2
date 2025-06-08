from typing import Any
from uuid import UUID, uuid4

import pytest
from freezegun import freeze_time
from starlette import status

from app.common.utils.datetime import datetime_utc_now
from app.messenger.models.chats_db import Chat
from app.messenger.models.messages_db import Message
from tests.common.active_session import ActiveSession
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.messenger import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_message_sending(
    active_session: ActiveSession,
    chat: Chat,
    chat_room_listener: TMEXIOTestClient,
    sender_user_id: int,
    tmexio_sender_client: TMEXIOTestClient,
) -> None:
    message_input_data = factories.MessageInputFactory.build_json()

    message_id: UUID = assert_ack(
        await tmexio_sender_client.emit(
            "send-chat-message",
            chat_id=chat.id,
            data=message_input_data,
        ),
        expected_code=201,
        expected_data={
            **message_input_data,
            "id": UUID,
            "sender_user_id": sender_user_id,
            "created_at": datetime_utc_now(),
            "updated_at": None,
        },
    )[1]["id"]
    tmexio_sender_client.assert_no_more_events()

    chat_room_listener.assert_next_event(
        expected_name="send-chat-message",
        expected_data={
            **message_input_data,
            "id": message_id,
            "sender_user_id": sender_user_id,
            "created_at": datetime_utc_now(),
            "updated_at": None,
            "chat_id": chat.id,
        },
    )
    chat_room_listener.assert_no_more_events()

    async with active_session():
        message = await Message.find_first_by_id(message_id)
        assert message is not None
        await message.delete()


@freeze_time()
async def test_my_message_updating(
    chat: Chat,
    chat_room_listener: TMEXIOTestClient,
    tmexio_sender_client: TMEXIOTestClient,
    message: Message,
    message_data: AnyJSON,
) -> None:
    message_patch_data = factories.MessageInputFactory.build_json()

    assert_ack(
        await tmexio_sender_client.emit(
            "edit-chat-message-content",
            chat_id=chat.id,
            message_id=message.id,
            data=message_patch_data,
        ),
        expected_data={
            **message_data,
            **message_patch_data,
            "updated_at": datetime_utc_now(),
        },
    )
    tmexio_sender_client.assert_no_more_events()

    chat_room_listener.assert_next_event(
        expected_name="edit-chat-message-content",
        expected_data={
            **message_data,
            **message_patch_data,
            "updated_at": datetime_utc_now(),
            "chat_id": chat.id,
        },
    )
    chat_room_listener.assert_no_more_events()


async def test_my_message_deleting(
    active_session: ActiveSession,
    chat: Chat,
    chat_room_listener: TMEXIOTestClient,
    tmexio_sender_client: TMEXIOTestClient,
    message: Message,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            "delete-my-chat-message",
            chat_id=chat.id,
            message_id=message.id,
        ),
        expected_code=204,
    )
    tmexio_sender_client.assert_no_more_events()

    chat_room_listener.assert_next_event(
        expected_name="delete-chat-message",
        expected_data={"chat_id": chat.id, "message_id": message.id},
    )
    chat_room_listener.assert_no_more_events()

    async with active_session():
        assert (await Message.find_first_by_id(message.id)) is None


my_messages_events_params = [
    pytest.param("send-chat-message", factories.MessageInputFactory, id="send"),
    pytest.param(
        "edit-chat-message-content", factories.MessageInputFactory, id="edit-content"
    ),
    pytest.param("delete-my-chat-message", None, id="delete"),
]


@pytest.mark.parametrize(("event_name", "data_factory"), my_messages_events_params)
async def test_chat_not_finding_for_my_messages(
    deleted_chat_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    chat_room_listener: TMEXIOTestClient,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            chat_id=deleted_chat_id,
            message_id=uuid4(),
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Chat not found",
    )
    tmexio_outsider_client.assert_no_more_events()
    chat_room_listener.assert_no_more_events()


# TODO test access to chat


@pytest.mark.parametrize(
    ("event_name", "data_factory"),
    [param for param in my_messages_events_params if param.id != "send"],
)
async def test_managing_my_messages_not_your_message(
    chat: Chat,
    tmexio_outsider_client: TMEXIOTestClient,
    chat_room_listener: TMEXIOTestClient,
    message: Message,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            chat_id=chat.id,
            message_id=message.id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="Message is not yours",
    )
    tmexio_outsider_client.assert_no_more_events()
    chat_room_listener.assert_no_more_events()


@pytest.mark.parametrize(
    ("event_name", "data_factory"),
    [param for param in my_messages_events_params if param.id != "send"],
)
async def test_message_not_finding_for_my_messages(
    chat: Chat,
    tmexio_sender_client: TMEXIOTestClient,
    chat_room_listener: TMEXIOTestClient,
    deleted_message_id: int,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            event_name,
            chat_id=chat.id,
            message_id=deleted_message_id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Message not found",
    )
    tmexio_sender_client.assert_no_more_events()
    chat_room_listener.assert_no_more_events()
