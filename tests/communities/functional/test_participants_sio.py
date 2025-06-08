import pytest
from starlette import status

from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant
from app.communities.rooms import (
    community_room,
    participant_room,
    participants_list_room,
)
from tests.common.active_session import ActiveSession
from tests.common.tmexio_testing import (
    TMEXIOListenerFactory,
    TMEXIOTestClient,
    assert_ack,
)
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_participants_listing(
    community: Community,
    participant_data: Participant,
    participants_data: list[AnyJSON],
    tmexio_participant_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            "list-participants",
            community_id=community.id,
        ),
        expected_data=sorted(
            participants_data + [participant_data],
            key=lambda participant: participant["created_at"],
            reverse=True,
        ),
    )
    tmexio_participant_client.assert_no_more_events()

    assert (
        participants_list_room(community.id)
        in tmexio_participant_client.current_rooms()
    )


async def test_participants_listing_community_not_found(
    deleted_community_id: int, tmexio_outsider_client: TMEXIOTestClient
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            "list-participants",
            community_id=deleted_community_id,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()


async def check_participants_list_closed(
    tmexio_client: TMEXIOTestClient, community_id: int
) -> None:
    await tmexio_client.enter_room(participants_list_room(community_id))

    assert_ack(
        await tmexio_client.emit(
            "close-participants",
            community_id=community_id,
        ),
        expected_code=status.HTTP_204_NO_CONTENT,
    )
    tmexio_client.assert_no_more_events()

    assert participants_list_room(community_id) not in tmexio_client.current_rooms()


async def test_participants_list_closing(
    community: Community, tmexio_owner_client: TMEXIOTestClient
) -> None:
    await check_participants_list_closed(
        tmexio_client=tmexio_owner_client, community_id=community.id
    )


async def test_participants_list_closing_deleted_participant(
    community: Community, tmexio_outsider_client: TMEXIOTestClient
) -> None:
    await check_participants_list_closed(
        tmexio_client=tmexio_outsider_client, community_id=community.id
    )


async def test_participants_list_closing_deleted_community(
    deleted_community_id: int, tmexio_outsider_client: TMEXIOTestClient
) -> None:
    await check_participants_list_closed(
        tmexio_client=tmexio_outsider_client, community_id=deleted_community_id
    )


async def test_participant_kicking(
    active_session: ActiveSession,
    tmexio_listener_factory: TMEXIOListenerFactory,
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    participant: Participant,
    tmexio_participant_client: TMEXIOTestClient,
) -> None:
    await tmexio_participant_client.enter_room(community_room(community.id))
    await tmexio_participant_client.enter_room(participants_list_room(community.id))

    participant_room_listener = await tmexio_listener_factory(
        participant_room(community.id, participant.user_id)
    )
    participant_list_room_listener = await tmexio_listener_factory(
        participants_list_room(community.id)
    )

    assert_ack(
        await tmexio_owner_client.emit(
            "kick-participant",
            community_id=community.id,
            target_user_id=participant.user_id,
        ),
        expected_code=status.HTTP_204_NO_CONTENT,
    )
    tmexio_owner_client.assert_no_more_events()

    participant_room_listener.assert_next_event(
        expected_name="kicked-from-community",
        expected_data={"community_id": community.id},
    )
    participant_room_listener.assert_no_more_events()

    participant_list_room_listener.assert_next_event(
        expected_name="delete-participant",
        expected_data={"community_id": community.id, "user_id": participant.user_id},
    )
    participant_list_room_listener.assert_no_more_events()

    assert community_room(community.id) not in tmexio_participant_client.current_rooms()
    assert (
        participants_list_room(community.id)
        not in tmexio_participant_client.current_rooms()
    )
    assert (
        participant_room(community.id, participant.user_id)
        not in participant_room_listener.current_rooms()
    )

    async with active_session():
        assert (
            await Participant.find_first_by_kwargs(
                community_id=community.id, user_id=participant.user_id
            )
            is None
        )


async def test_participant_kicking_participant_not_found(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    deleted_participant_id: int,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "kick-participant",
            community_id=community.id,
            target_user_id=deleted_participant_id,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Participant not found",
    )
    tmexio_owner_client.assert_no_more_events()


async def test_participant_kicking_target_is_the_source(
    community: Community,
    owner_proxy_auth_data: Participant,
    tmexio_owner_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "kick-participant",
            community_id=community.id,
            target_user_id=owner_proxy_auth_data.user_id,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_data="Target is the source",
    )
    tmexio_owner_client.assert_no_more_events()


@pytest.mark.parametrize(
    "event_name",
    [
        pytest.param("list-participants", id="list"),
        pytest.param("kick-participant", id="kick"),
    ],
)
async def test_participants_listing_no_access_to_community(
    community: Community,
    participant_user_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=community.id,
            target_user_id=participant_user_id,
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="No access to community",
    )
    tmexio_outsider_client.assert_no_more_events()


async def test_participant_kicking_not_sufficient_permissions(
    community: Community,
    participant: Participant,
    tmexio_participant_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            "kick-participant",
            community_id=community.id,
            target_user_id=participant.id,
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="Not sufficient permissions",
    )
    tmexio_participant_client.assert_no_more_events()
