import pytest
from starlette import status
from starlette.testclient import TestClient

from app.communities.models.chat_channels_db import ChatChannel
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


async def test_chat_channel_retrieving(
    mub_client: TestClient,
    chat_channel: ChatChannel,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/channels/{chat_channel.id}/chat/"),
        expected_json={"chat_id": chat_channel.chat_id},
    )


async def test_chat_channel_retrieving_chat_channel_not_found(
    mub_client: TestClient,
    deleted_chat_channel_id: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/channels/{deleted_chat_channel_id}/chat/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Chat-channel not found"},
    )
