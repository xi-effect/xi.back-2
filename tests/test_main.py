import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from socketio import packet as sio_packet  # type: ignore[import-untyped]

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.communities.rooms import user_room
from app.communities.store import user_id_to_sids
from tests.common.tmexio_testing import TMEXIOTestServer

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_socketio_connection(
    proxy_auth_data: ProxyAuthData,
    tmexio_server: TMEXIOTestServer,
) -> None:
    # on_connect
    async with tmexio_server.authorized_client(proxy_auth_data) as client:
        assert user_id_to_sids[proxy_auth_data.user_id] == {client.sio_sid}

        assert user_room(proxy_auth_data.user_id) in client.current_rooms()

    # on_disconnect
    assert user_id_to_sids[proxy_auth_data.user_id] == set()


async def test_socketio_connection_unauthorized(
    tmexio_server: TMEXIOTestServer,
) -> None:
    async with tmexio_server.client() as client:
        assert len(client.sio_packets) == 1
        assert_contains(
            client.sio_packets[0],
            {
                "packet_type": sio_packet.CONNECT_ERROR,
                "data": {"message": "(407, 'bad')"},
                "attachment_count": 0,
            },
        )

        assert set.union(*user_id_to_sids.values()) == set()
