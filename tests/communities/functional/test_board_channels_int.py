import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.config import API_KEY
from app.common.dependencies.api_key_dep import API_KEY_HEADER_NAME
from app.common.dependencies.authorization_dep import (
    AUTH_SESSION_ID_HEADER_NAME,
    AUTH_USER_ID_HEADER_NAME,
    AUTH_USERNAME_HEADER_NAME,
    ProxyAuthData,
)
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response

pytestmark = pytest.mark.anyio


@pytest.fixture()
def authorized_internal_client(
    proxy_auth_data: ProxyAuthData, client: TestClient
) -> TestClient:
    return TestClient(
        client.app,
        headers={
            AUTH_SESSION_ID_HEADER_NAME: str(proxy_auth_data.session_id),
            AUTH_USER_ID_HEADER_NAME: str(proxy_auth_data.user_id),
            AUTH_USERNAME_HEADER_NAME: proxy_auth_data.username,
            API_KEY_HEADER_NAME: API_KEY,
        },
    )


@pytest.mark.parametrize(
    "is_owner",
    [
        pytest.param(True, id="owner"),
        pytest.param(False, id="participant"),
    ],
)
async def test_board_channel_access_level_retrieving(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    community: Community,
    board_channel: BoardChannel,
    authorized_internal_client: TestClient,
    is_owner: bool,
) -> None:
    async with active_session():
        await Participant.create(
            community_id=community.id,
            user_id=proxy_auth_data.user_id,
            is_owner=is_owner,
        )

    assert_response(
        authorized_internal_client.get(
            f"/internal/community-service/channels/{board_channel.id}/board/access-level/",
        ),
        expected_json={"write_access": is_owner},
    )


async def test_board_channel_access_level_retrieving_access_denied(
    board_channel: BoardChannel, authorized_internal_client: TestClient
) -> None:
    assert_response(
        authorized_internal_client.get(
            f"/internal/community-service/channels/{board_channel.id}/board/access-level/",
        ),
        expected_code=403,
        expected_json={"detail": "No access to community"},
    )


async def test_board_channel_access_level_retrieving_proxy_auth_required(
    internal_client: TestClient, board_channel: BoardChannel
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/community-service/channels/{board_channel.id}/board/access-level/",
        ),
        expected_code=407,
        expected_json={"detail": "Proxy auth required"},
    )


async def test_board_channel_content_retrieving(
    internal_client: TestClient, board_channel: BoardChannel
) -> None:
    response = assert_response(
        internal_client.get(
            f"/internal/community-service/channels/{board_channel.id}/board/content/",
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
    internal_client: TestClient,
    board_channel: BoardChannel,
) -> None:
    content: bytes = faker.binary(length=64)

    assert_nodata_response(
        internal_client.put(
            f"/internal/community-service/channels/{board_channel.id}/board/content/",
            content=content,
            headers={"Content-Type": "application/octet-stream"},
        ),
    )

    async with active_session():
        updated_board_channel = await BoardChannel.find_first_by_id(board_channel.id)
        assert updated_board_channel is not None
        assert updated_board_channel.content == content


@pytest.mark.parametrize(
    ("method", "with_content", "path"),
    [
        pytest.param("GET", False, "content", id="retrieve-content"),
        pytest.param("PUT", True, "content", id="update-content"),
        pytest.param("GET", False, "access-level", id="retrieve-access-level"),
    ],
)
async def test_board_channel_not_finding(
    faker: Faker,
    deleted_board_channel_id: int,
    authorized_internal_client: TestClient,
    method: str,
    with_content: bool,
    path: str,
) -> None:
    assert_response(
        authorized_internal_client.request(
            method,
            f"/internal/community-service/channels/{deleted_board_channel_id}/board/{path}/",
            content=faker.binary(length=64) if with_content else None,
            headers=(
                {"Content-Type": "application/octet-stream"} if with_content else None
            ),
        ),
        expected_code=404,
        expected_json={"detail": "Board-channel not found"},
    )
