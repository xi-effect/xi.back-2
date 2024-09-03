import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.communities.models.board_channels_db import BoardChannel
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response

pytestmark = pytest.mark.anyio


async def test_board_channel_content_retrieving(
    mub_client: TestClient,
    board_channel: BoardChannel,
) -> None:
    response = assert_response(
        mub_client.get(
            f"/mub/community-service/channels/{board_channel.id}/board/content/",
        ),
        expected_json=None,
        expected_headers={
            "Content-Type": "application/octet-stream",
        },
    )
    assert response.content == board_channel.content


async def test_board_channel_content_updating(
    faker: Faker,
    active_session: ActiveSession,
    mub_client: TestClient,
    board_channel: BoardChannel,
) -> None:
    content: bytes = faker.binary(length=64)

    assert_nodata_response(
        mub_client.put(
            f"/mub/community-service/channels/{board_channel.id}/board/content/",
            content=content,
            headers={"Content-Type": "application/octet-stream"},
        ),
    )

    async with active_session():
        updated_board_channel = await BoardChannel.find_first_by_id(board_channel.id)
        assert updated_board_channel is not None
        assert updated_board_channel.content == content


@pytest.mark.parametrize(
    ("method", "pass_content"),
    [
        pytest.param("GET", False, id="retrieve"),
        pytest.param("PUT", True, id="update"),
    ],
)
async def test_board_channel_not_finding(
    faker: Faker,
    mub_client: TestClient,
    deleted_board_channel_id: int,
    method: str,
    pass_content: bool,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/channels/{deleted_board_channel_id}/board/content/",
            content=faker.binary(length=64) if pass_content else None,
            headers=(
                {"Content-Type": "application/octet-stream"} if pass_content else None
            ),
        ),
        expected_code=404,
        expected_json={"detail": "Board-channel not found"},
    )
