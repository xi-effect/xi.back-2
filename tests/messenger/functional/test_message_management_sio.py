from uuid import uuid4

import pytest

from app.messenger.models.chats_db import Chat
from app.messenger.models.messages_db import Message
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack

pytestmark = pytest.mark.anyio


async def test_message_pinning(
    chat: Chat,
    chat_room_listener: TMEXIOTestClient,
    tmexio_sender_client: TMEXIOTestClient,
    message: Message,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            "pin-chat-message",
            chat_id=chat.id,
            message_id=message.id,
        ),
        expected_code=204,
    )
    tmexio_sender_client.assert_no_more_events()

    chat_room_listener.assert_next_event(
        expected_name="pin-chat-message",
        expected_data={
            "chat_id": chat.id,
            "message_id": message.id,
        },
    )
    chat_room_listener.assert_no_more_events()


async def test_message_pinning_already_pinned(
    chat: Chat,
    chat_room_listener: TMEXIOTestClient,
    tmexio_sender_client: TMEXIOTestClient,
    pinned_message: Message,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            "pin-chat-message",
            chat_id=chat.id,
            message_id=pinned_message.id,
        ),
        expected_code=409,
        expected_data="Message is already pinned",
    )
    tmexio_sender_client.assert_no_more_events()
    chat_room_listener.assert_no_more_events()


async def test_message_unpinning(
    chat: Chat,
    chat_room_listener: TMEXIOTestClient,
    tmexio_sender_client: TMEXIOTestClient,
    pinned_message: Message,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            "unpin-chat-message",
            chat_id=chat.id,
            message_id=pinned_message.id,
        ),
        expected_code=204,
    )
    tmexio_sender_client.assert_no_more_events()

    chat_room_listener.assert_next_event(
        expected_name="unpin-chat-message",
        expected_data={
            "chat_id": chat.id,
            "message_id": pinned_message.id,
        },
    )
    chat_room_listener.assert_no_more_events()


async def test_message_unpinning_not_pinned(
    chat: Chat,
    chat_room_listener: TMEXIOTestClient,
    tmexio_sender_client: TMEXIOTestClient,
    message: Message,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            "unpin-chat-message",
            chat_id=chat.id,
            message_id=message.id,
        ),
        expected_code=409,
        expected_data="Message is not pinned",
    )
    tmexio_sender_client.assert_no_more_events()
    chat_room_listener.assert_no_more_events()


message_management_events_params = [
    pytest.param("pin-chat-message", id="pin"),
    pytest.param("unpin-chat-message", id="unpin"),
]


@pytest.mark.parametrize("event_name", message_management_events_params)
async def test_chat_not_finding_for_my_messages(
    deleted_chat_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    chat_room_listener: TMEXIOTestClient,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            chat_id=deleted_chat_id,
            message_id=uuid4(),
        ),
        expected_code=404,
        expected_data="Chat not found",
    )
    tmexio_outsider_client.assert_no_more_events()
    chat_room_listener.assert_no_more_events()


# TODO test access to chat


@pytest.mark.parametrize("event_name", message_management_events_params)
async def test_message_not_finding_for_message_management(
    chat: Chat,
    tmexio_sender_client: TMEXIOTestClient,
    chat_room_listener: TMEXIOTestClient,
    deleted_message_id: int,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            event_name,
            chat_id=chat.id,
            message_id=deleted_message_id,
        ),
        expected_code=404,
        expected_data="Message not found",
    )
    tmexio_sender_client.assert_no_more_events()
    chat_room_listener.assert_no_more_events()
