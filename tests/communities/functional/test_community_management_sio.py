from typing import Any

import pytest

from app.communities.models.communities_db import Community
from app.communities.rooms import community_room, participants_list_room
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.communities.factories import CommunityFullPatchFactory

pytestmark = pytest.mark.anyio


async def test_community_updating(
    community_data: AnyJSON,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
) -> None:
    community_patch_data = CommunityFullPatchFactory.build_json()

    assert_ack(
        await tmexio_owner_client.emit(
            "update-community",
            data=community_patch_data,
            community_id=community.id,
        ),
        expected_data={**community_data, **community_patch_data, "id": community.id},
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="update-community",
        expected_data={**community_data, **community_patch_data, "id": community.id},
    )
    community_room_listener.assert_no_more_events()


async def test_community_deleting(
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit("delete-community", community_id=community.id),
        expected_code=204,
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="delete-community",
        expected_data={"community_id": community.id},
    )
    community_room_listener.assert_no_more_events()

    for client in (tmexio_owner_client, community_room_listener):
        assert community_room(community.id) not in client.current_rooms()
        assert participants_list_room(community.id) not in client.current_rooms()


management_events_parametrization = pytest.mark.parametrize(
    ("event_name", "data_factory"),
    [
        pytest.param("update-community", CommunityFullPatchFactory, id="update"),
        pytest.param("delete-community", None, id="delete"),
    ],
)


@management_events_parametrization
async def test_community_management_community_not_found(
    deleted_community_id: int,
    community_room_listener: TMEXIOTestClient,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=deleted_community_id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_data="Community not found",
        expected_code=404,
    )
    tmexio_outsider_client.assert_no_more_events()
    community_room_listener.assert_no_more_events()


@management_events_parametrization
async def test_community_management_insufficient_permissions(
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_participant_client: TMEXIOTestClient,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            event_name,
            community_id=community.id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_data="Not sufficient permissions",
        expected_code=403,
    )
    tmexio_participant_client.assert_no_more_events()
    community_room_listener.assert_no_more_events()


@management_events_parametrization
async def test_community_management_no_access_to_community(
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=community.id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_data="No access to community",
        expected_code=403,
    )
    tmexio_outsider_client.assert_no_more_events()
    community_room_listener.assert_no_more_events()
