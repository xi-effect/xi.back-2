from collections.abc import AsyncIterator

import pytest

from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant
from app.communities.rooms import (
    community_room,
    participant_room,
    participants_list_room,
)
from tests.common.active_session import ActiveSession
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.communities import factories

pytestmark = pytest.mark.anyio

COMMUNITY_LIST_SIZE = 6


@pytest.fixture()
async def communities_data(
    active_session: ActiveSession,
    outsider_user_id: int,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        communities = [
            await Community.create(**factories.CommunityFullInputFactory.build_json())
            for _ in range(COMMUNITY_LIST_SIZE)
        ]
        for i, community in enumerate(communities):
            await Participant.create(
                community_id=community.id,
                user_id=outsider_user_id,
                is_owner=i % 2 == 0,
            )
    # if ordering will be added:
    # `communities.sort(key=lambda community: community.created_at)`

    yield [
        Community.FullResponseSchema.model_validate(
            community, from_attributes=True
        ).model_dump(mode="json")
        for community in communities
    ]

    async with active_session():
        for community in communities:
            await community.delete()


async def test_community_listing(
    tmexio_outsider_client: TMEXIOTestClient,
    communities_data: list[AnyJSON],
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit("list-communities"),
        expected_data=communities_data,
    )
    tmexio_outsider_client.assert_no_more_events()


async def test_community_listing_empty_list(
    tmexio_outsider_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit("list-communities"),
        expected_data=[],
    )
    tmexio_outsider_client.assert_no_more_events()


async def test_any_community_retrieving_and_opening(
    community_data: AnyJSON,
    community: Community,
    actor_is_owner: bool,
    actor_user_id: int,
    tmexio_actor_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_actor_client.emit("retrieve-any-community"),
        expected_data={
            "community": {"id": community.id, **community_data},
            "participant": {"is_owner": actor_is_owner},
        },
    )
    tmexio_actor_client.assert_no_more_events()

    assert community_room(community.id) in tmexio_actor_client.current_rooms()
    assert (
        participant_room(community.id, actor_user_id)
        in tmexio_actor_client.current_rooms()
    )


async def test_any_community_retrieving_and_opening_no_communities(
    outsider_user_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
) -> None:
    old_rooms = tmexio_outsider_client.current_rooms()

    assert_ack(
        await tmexio_outsider_client.emit("retrieve-any-community"),
        expected_code=404,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()

    assert tmexio_outsider_client.current_rooms() == old_rooms


async def test_community_retrieving_and_opening(
    community_data: AnyJSON,
    community: Community,
    actor_is_owner: bool,
    actor_user_id: int,
    tmexio_actor_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_actor_client.emit("retrieve-community", community_id=community.id),
        expected_data={
            "community": {"id": community.id, **community_data},
            "participant": {"is_owner": actor_is_owner},
        },
    )
    tmexio_actor_client.assert_no_more_events()

    assert community_room(community.id) in tmexio_actor_client.current_rooms()
    assert (
        participant_room(community.id, actor_user_id)
        in tmexio_actor_client.current_rooms()
    )


async def test_community_retrieving_and_opening_community_not_found(
    deleted_community_id: int,
    outsider_user_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            "retrieve-community", community_id=deleted_community_id
        ),
        expected_code=404,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()

    assert (
        community_room(deleted_community_id)
        not in tmexio_outsider_client.current_rooms()
    )
    assert (
        participant_room(deleted_community_id, outsider_user_id)
        not in tmexio_outsider_client.current_rooms()
    )


async def test_community_retrieving_and_opening_no_access_to_community(
    community: Community,
    outsider_user_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            "retrieve-community", community_id=community.id
        ),
        expected_code=403,
        expected_data="No access to community",
    )
    tmexio_outsider_client.assert_no_more_events()

    assert community_room(community.id) not in tmexio_outsider_client.current_rooms()
    assert (
        participant_room(community.id, outsider_user_id)
        not in tmexio_outsider_client.current_rooms()
    )


async def check_community_closed(
    tmexio_client: TMEXIOTestClient, community_id: int, user_id: int
) -> None:
    room_names = [
        community_room(community_id),
        participants_list_room(community_id),
        participant_room(community_id, user_id),
    ]

    for room_name in room_names:
        await tmexio_client.enter_room(room_name)

    assert_ack(
        await tmexio_client.emit("close-community", community_id=community_id),
        expected_code=204,
    )
    tmexio_client.assert_no_more_events()

    for room_name in room_names:
        assert room_name not in tmexio_client.current_rooms()


async def test_community_closing(
    community: Community,
    tmexio_actor_client: TMEXIOTestClient,
    actor_user_id: int,
) -> None:
    await check_community_closed(
        tmexio_client=tmexio_actor_client,
        community_id=community.id,
        user_id=actor_user_id,
    )


async def test_community_closing_deleted_participant(
    community: Community,
    tmexio_outsider_client: TMEXIOTestClient,
    outsider_user_id: int,
) -> None:
    await check_community_closed(
        tmexio_client=tmexio_outsider_client,
        community_id=community.id,
        user_id=outsider_user_id,
    )


async def test_community_closing_deleted_community(
    deleted_community_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    outsider_user_id: int,
) -> None:
    await check_community_closed(
        tmexio_client=tmexio_outsider_client,
        community_id=deleted_community_id,
        user_id=outsider_user_id,
    )
