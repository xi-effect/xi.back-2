import pytest
from jwt import decode
from pydantic_marshals.contains import assert_contains
from starlette import status

from app.common.config import settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.communities.models.call_channels_db import CallChannel
from app.communities.models.communities_db import Community
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack

pytestmark = pytest.mark.anyio


async def test_call_channel_livekit_token_generating(
    community: Community,
    participant_proxy_auth_data: ProxyAuthData,
    tmexio_participant_client: TMEXIOTestClient,
    call_channel: CallChannel,
) -> None:
    token: str = assert_ack(
        await tmexio_participant_client.emit(
            "generate-livekit-token",
            community_id=community.id,
            channel_id=call_channel.id,
        ),
        expected_data=str,
    )[1]

    assert_contains(
        decode(token, settings.livekit_api_secret, algorithms=["HS256"]),
        {
            "sub": str(participant_proxy_auth_data.user_id),
            "name": participant_proxy_auth_data.username,
            "video": {"room": f"call-channel-room-{call_channel.id}"},
        },
    )
    tmexio_participant_client.assert_no_more_events()


async def test_call_channel_livekit_token_generating_call_channel_not_found(
    community: Community,
    tmexio_participant_client: TMEXIOTestClient,
    deleted_call_channel_id: int,
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            "generate-livekit-token",
            community_id=community.id,
            channel_id=deleted_call_channel_id,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Call-channel not found",
    )
    tmexio_participant_client.assert_no_more_events()


async def test_call_channel_livekit_token_generating_community_not_found(
    deleted_community_id: int, tmexio_outsider_client: TMEXIOTestClient
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            "generate-livekit-token",
            community_id=deleted_community_id,
            channel_id=1,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()


async def test_call_channel_livekit_token_generating_no_access_to_community(
    community: Community, tmexio_outsider_client: TMEXIOTestClient
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            "generate-livekit-token",
            community_id=community.id,
            channel_id=1,
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="No access to community",
    )
    tmexio_outsider_client.assert_no_more_events()
