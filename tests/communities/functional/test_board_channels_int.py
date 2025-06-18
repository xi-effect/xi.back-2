import pytest
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.storage_sch import YDocAccessLevel
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("is_owner", "access_level"),
    [
        pytest.param(True, YDocAccessLevel.READ_WRITE, id="owner"),
        pytest.param(False, YDocAccessLevel.READ_ONLY, id="participant"),
    ],
)
async def test_board_channel_access_level_retrieving(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    authorized_internal_client: TestClient,
    community: Community,
    board_channel: BoardChannel,
    is_owner: bool,
    access_level: YDocAccessLevel,
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
        expected_json=access_level,
    )


async def test_board_channel_access_level_retrieving_no_access(
    authorized_internal_client: TestClient,
    board_channel: BoardChannel,
) -> None:
    assert_response(
        authorized_internal_client.get(
            f"/internal/community-service/channels/{board_channel.id}/board/access-level/",
        ),
        expected_json=YDocAccessLevel.NO_ACCESS,
    )


async def test_board_channel_access_level_retrieving_proxy_auth_required(
    internal_client: TestClient,
    board_channel: BoardChannel,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/community-service/channels/{board_channel.id}/board/access-level/",
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Proxy auth required"},
    )


async def test_board_channel_access_level_retrieving_board_channel_not_found(
    authorized_internal_client: TestClient,
    deleted_board_channel_id: int,
) -> None:
    assert_response(
        authorized_internal_client.get(
            f"/internal/community-service/channels/{deleted_board_channel_id}/board/access-level/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Board-channel not found"},
    )
