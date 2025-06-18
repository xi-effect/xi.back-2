import pytest
from starlette import status
from starlette.testclient import TestClient

from app.communities.models.board_channels_db import BoardChannel
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_board_channel_retrieving(
    mub_client: TestClient,
    board_channel: BoardChannel,
    board_channel_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/channels/{board_channel.id}/board/"),
        expected_json=board_channel_data,
    )


async def test_board_channel_retrieving_board_channel_not_found(
    mub_client: TestClient,
    deleted_board_channel_id: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/channels/{deleted_board_channel_id}/board/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Board-channel not found"},
    )
