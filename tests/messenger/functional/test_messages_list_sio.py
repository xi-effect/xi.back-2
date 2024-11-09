import pytest

from app.common.utils.datetime import datetime_utc_now
from app.messenger.models.chats_db import Chat
from app.messenger.rooms import chat_room
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.messenger.conftest import MESSAGE_LIST_SIZE

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "limit",
    [
        pytest.param(MESSAGE_LIST_SIZE, id="start_to_end"),
        pytest.param(MESSAGE_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_latest_messages_listing(
    chat: Chat,
    tmexio_sender_client: TMEXIOTestClient,
    messages_data: list[AnyJSON],
    limit: int,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            "list-latest-chat-messages",
            chat_id=chat.id,
            limit=limit,
        ),
        expected_data=messages_data[:limit],
    )
    tmexio_sender_client.assert_no_more_events()

    assert chat_room(chat.id) in tmexio_sender_client.current_rooms()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(1, MESSAGE_LIST_SIZE, id="second_to_end"),
        pytest.param(1, MESSAGE_LIST_SIZE // 2, id="second_to_middle"),
        pytest.param(MESSAGE_LIST_SIZE // 2, MESSAGE_LIST_SIZE, id="middle_to_end"),
    ],
)
async def test_message_history_listing(
    chat: Chat,
    tmexio_sender_client: TMEXIOTestClient,
    messages_data: list[AnyJSON],
    offset: int,
    limit: int,
) -> None:
    created_before = messages_data[offset - 1]["created_at"]

    assert_ack(
        await tmexio_sender_client.emit(
            "list-chat-messages",
            chat_id=chat.id,
            created_before=created_before,
            limit=limit,
        ),
        expected_data=messages_data[offset : limit + 1],
    )


message_list_events_params = [
    pytest.param("list-latest-chat-messages", id="list-latest"),
    pytest.param("list-chat-messages", id="list-history"),
]


@pytest.mark.parametrize("event_name", message_list_events_params)
async def test_chat_not_finding_for_messages_list(
    deleted_chat_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    chat_room_listener: TMEXIOTestClient,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            chat_id=deleted_chat_id,
            created_before=datetime_utc_now(),
            limit=100,
        ),
        expected_code=404,
        expected_data="Chat not found",
    )
    tmexio_outsider_client.assert_no_more_events()


# TODO test access to chat


async def check_participants_list_closed(
    tmexio_client: TMEXIOTestClient, chat_id: int
) -> None:
    await tmexio_client.enter_room(chat_room(chat_id))

    assert_ack(
        await tmexio_client.emit("close-chat", chat_id=chat_id),
        expected_code=204,
    )
    tmexio_client.assert_no_more_events()

    assert chat_room(chat_id) not in tmexio_client.current_rooms()


async def test_chat_closing(chat: Chat, tmexio_sender_client: TMEXIOTestClient) -> None:
    await check_participants_list_closed(
        tmexio_client=tmexio_sender_client, chat_id=chat.id
    )


# TODO test_chat_closing_deleted_user


async def test_chat_closing_deleted_chat(
    deleted_chat_id: int, tmexio_outsider_client: TMEXIOTestClient
) -> None:
    await check_participants_list_closed(
        tmexio_client=tmexio_outsider_client, chat_id=deleted_chat_id
    )
