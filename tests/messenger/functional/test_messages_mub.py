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
from tests.common.utils import remove_none_values
from tests.messenger.conftest import MESSAGE_LIST_SIZE
from tests.messenger.factories import (
    MessageInputFactory,
    MessageInputMUBFactory,
    MessagePatchMUBFactory,
)

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "limit",
    [
        pytest.param(MESSAGE_LIST_SIZE, id="start_to_end"),
        pytest.param(MESSAGE_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_latest_messages_listing(
    mub_client: TestClient,
    chat: Chat,
    messages_data: list[AnyJSON],
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/messenger-service/chats/{chat.id}/messages/",
            params={"limit": limit},
        ),
        expected_json=messages_data[:limit],
    )


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(1, MESSAGE_LIST_SIZE, id="second_to_end"),
        pytest.param(1, MESSAGE_LIST_SIZE // 2, id="second_to_middle"),
        pytest.param(MESSAGE_LIST_SIZE // 2, MESSAGE_LIST_SIZE, id="middle_to_end"),
    ],
)
async def test_message_history_listing(
    mub_client: TestClient,
    chat: Chat,
    messages_data: list[AnyJSON],
    offset: int,
    limit: int,
) -> None:
    created_before = messages_data[offset - 1]["created_at"]

    assert_response(
        mub_client.get(
            f"/mub/messenger-service/chats/{chat.id}/messages/",
            params={"created_before": created_before, "limit": limit},
        ),
        expected_json=messages_data[offset : limit + 1],
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
    mub_client: TestClient,
    chat: Chat,
    messages_data: list[AnyJSON],
    from_start: bool,
    limit: int,
) -> None:
    offset = 0 if from_start else 1
    messages_data = [
        message_data for message_data in messages_data if message_data["pinned"]
    ]

    assert_response(
        mub_client.get(
            f"/mub/messenger-service/chats/{chat.id}/messages/",
            params=remove_none_values(
                {
                    "created_before": (
                        None if from_start else messages_data[0]["created_at"]
                    ),
                    "limit": limit,
                    "only_pinned": True,
                }
            ),
        ),
        expected_json=messages_data[offset : offset + limit],
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
async def test_chat_not_finding_for_mub_messages(
    mub_client: TestClient,
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


@pytest.mark.parametrize(
    "set_updated_at",
    [
        pytest.param(True, id="set_updated_at"),
        pytest.param(False, id="keep_updated_at"),
    ],
)
@freeze_time()
async def test_message_updating(
    mub_client: TestClient,
    message: Message,
    message_data: AnyJSON,
    set_updated_at: bool,
) -> None:
    message_patch_data = MessagePatchMUBFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/messenger-service/messages/{message.id}/",
            params={"set_updated_at": set_updated_at},
            json=message_patch_data,
        ),
        expected_json={
            **message_data,
            **message_patch_data,
            **({"updated_at": datetime_utc_now()} if set_updated_at else {}),
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
        pytest.param("PATCH", MessageInputFactory, id="patch"),
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
