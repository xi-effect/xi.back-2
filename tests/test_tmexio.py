import pytest

from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack

pytestmark = pytest.mark.anyio


async def test_simple(
    tmexio_client_1: TMEXIOTestClient, tmexio_client_2: TMEXIOTestClient
) -> None:
    community_id = assert_ack(
        await tmexio_client_1.emit("create-community", data={"name": "wow"}),
        expected_data={
            "community": {"id": int, "name": "wow", "description": None},
            "participant": {"is_owner": True},
        },
    )[1]["community"]["id"]

    tmexio_client_2.assert_next_event(
        expected_name="create-community",
        expected_data={"id": community_id, "name": "wow", "description": None},
    )

    tmexio_client_1.assert_no_more_events()
    tmexio_client_2.assert_no_more_events()
