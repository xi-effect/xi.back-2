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
async def test_chat_opening(
    chat: Chat,
    tmexio_sender_client: TMEXIOTestClient,
    messages_data: list[AnyJSON],
    limit: int,
) -> None:
    assert_ack(
        await tmexio_sender_client.emit(
            "open-chat",
            chat_id=chat.id,
            limit=limit,
        ),
        expected_data={
            # TODO message_draft
            "latest_messages": messages_data[:limit],
        },
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
async def test_message_listing(
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


@pytest.mark.parametrize(
    "from_start",
    [
        pytest.param(True, id="from_start"),
        pytest.param(False, id="from_second"),
    ],
)
@pytest.mark.parametrize(
    "limit",
    [
        pytest.param(1, id="limit_1"),
        pytest.param(50, id="limit_50"),
    ],
)
async def test_pinned_message_listing(
    chat: Chat,
    tmexio_sender_client: TMEXIOTestClient,
    messages_data: list[AnyJSON],
    from_start: bool,
    limit: int,
) -> None:
    offset = 0 if from_start else 1
    messages_data = [
        message_data for message_data in messages_data if message_data["pinned"]
    ]

    assert_ack(
        await tmexio_sender_client.emit(
            "list-chat-pinned-messages",
            chat_id=chat.id,
            created_before=None if from_start else messages_data[0]["created_at"],
            limit=limit,
        ),
        expected_data=messages_data[offset : offset + limit],
    )


message_list_events_params = [
    pytest.param("open-chat", id="open"),
    pytest.param("list-chat-messages", id="list-history"),
    pytest.param("list-chat-pinned-messages", id="list-pinned"),
]


@pytest.mark.parametrize("event_name", message_list_events_params)
async def test_chat_not_finding_for_chats(
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


async def check_chat_closed(tmexio_client: TMEXIOTestClient, chat_id: int) -> None:
    await tmexio_client.enter_room(chat_room(chat_id))

    assert_ack(
        await tmexio_client.emit("close-chat", chat_id=chat_id),
        expected_code=204,
    )
    tmexio_client.assert_no_more_events()

    assert chat_room(chat_id) not in tmexio_client.current_rooms()


async def test_chat_closing(chat: Chat, tmexio_sender_client: TMEXIOTestClient) -> None:
    await check_chat_closed(tmexio_client=tmexio_sender_client, chat_id=chat.id)


# TODO test_chat_closing_deleted_user


async def test_chat_closing_deleted_chat(
    deleted_chat_id: int, tmexio_outsider_client: TMEXIOTestClient
) -> None:
    await check_chat_closed(
        tmexio_client=tmexio_outsider_client, chat_id=deleted_chat_id
    )
