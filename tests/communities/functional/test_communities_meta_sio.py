import pytest

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.communities.models.communities_db import Community
from app.communities.rooms import community_room, participant_room, user_room
from tests.common.active_session import ActiveSession
from tests.common.tmexio_testing import (
    TMEXIOListenerFactory,
    TMEXIOTestClient,
    assert_ack,
)
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_community_creation(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tmexio_actor_client: TMEXIOTestClient,
    tmexio_listener_factory: TMEXIOListenerFactory,
    community_data: AnyJSON,
) -> None:
    user_room_listener = await tmexio_listener_factory(
        user_room(proxy_auth_data.user_id)
    )

    community_id = assert_ack(
        await tmexio_actor_client.emit(
            "create-community",
            data=community_data,
        ),
        expected_data={
            "community": {"id": int, **community_data},
            "participant": {"is_owner": True},
        },
    )[1]["community"]["id"]

    assert community_room(community_id) in tmexio_actor_client.current_rooms()
    assert (
        participant_room(community_id, proxy_auth_data.user_id)
        in tmexio_actor_client.current_rooms()
    )

    user_room_listener.assert_next_event(
        expected_name="create-community",
        expected_data={"id": community_id, **community_data},
    )

    tmexio_actor_client.assert_no_more_events()
    user_room_listener.assert_no_more_events()

    async with active_session():
        community = await Community.find_first_by_id(community_id)
        assert community is not None
        await community.delete()
