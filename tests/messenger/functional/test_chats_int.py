import pytest
from starlette.testclient import TestClient

from app.messenger.models.chats_db import Chat
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_chat_channel_creation(
    active_session: ActiveSession,
    internal_client: TestClient,
    chat_data: AnyJSON,
) -> None:
    chat_id: int = assert_response(
        internal_client.post("/internal/messenger-service/chats/", json=chat_data),
        expected_code=201,
        expected_json={**chat_data, "id": int},
    ).json()["id"]

    async with active_session():
        chat = await Chat.find_first_by_id(chat_id)
        assert chat is not None
        await chat.delete()


async def test_chat_channel_deleting(
    active_session: ActiveSession,
    internal_client: TestClient,
    chat: Chat,
) -> None:
    assert_nodata_response(
        internal_client.delete(f"/internal/messenger-service/chats/{chat.id}/"),
    )

    async with active_session():
        assert await Chat.find_first_by_id(chat.id) is None


async def test_chat_channel_deleting_chat_not_found(
    internal_client: TestClient, deleted_chat_id: int
) -> None:
    assert_response(
        internal_client.delete(
            f"/internal/messenger-service/chats/{deleted_chat_id}/",
        ),
        expected_code=404,
        expected_json={"detail": "Chat not found"},
    )
