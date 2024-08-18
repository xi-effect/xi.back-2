import pytest

from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from app.communities.models.participants_db import Participant
from app.communities.rooms import (
    community_room,
    participant_room,
    participants_list_room,
    user_room,
)
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
    tmexio_listener_factory: TMEXIOListenerFactory,
    outsider_user_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    community_data: AnyJSON,
) -> None:
    user_room_listener = await tmexio_listener_factory(user_room(outsider_user_id))

    community_id = assert_ack(
        await tmexio_outsider_client.emit(
            "create-community",
            data=community_data,
        ),
        expected_data={
            "community": {"id": int, **community_data},
            "participant": {"is_owner": True},
        },
    )[1]["community"]["id"]
    tmexio_outsider_client.assert_no_more_events()

    assert community_room(community_id) in tmexio_outsider_client.current_rooms()
    assert (
        participant_room(community_id, outsider_user_id)
        in tmexio_outsider_client.current_rooms()
    )

    user_room_listener.assert_next_event(
        expected_name="create-community",
        expected_data={"id": community_id, **community_data},
    )
    user_room_listener.assert_no_more_events()

    async with active_session():
        community = await Community.find_first_by_id(community_id)
        assert community is not None
        await community.delete()


async def test_community_joining(
    active_session: ActiveSession,
    tmexio_listener_factory: TMEXIOListenerFactory,
    community_data: AnyJSON,
    community: Community,
    outsider_user_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    invitation: Invitation,
) -> None:
    usages_before = invitation.usage_count

    user_room_listener = await tmexio_listener_factory(user_room(outsider_user_id))
    participant_list_listener = await tmexio_listener_factory(
        participants_list_room(community.id)
    )

    assert_ack(
        await tmexio_outsider_client.emit("join-community", code=invitation.token),
        expected_data={
            "community": {"id": community.id, **community_data},
            "participant": {"is_owner": False},
        },
    )
    tmexio_outsider_client.assert_no_more_events()

    assert community_room(community.id) in tmexio_outsider_client.current_rooms()
    assert (
        participant_room(community.id, outsider_user_id)
        in tmexio_outsider_client.current_rooms()
    )

    async with active_session() as session:
        participant = await Participant.find_first_by_kwargs(
            community_id=community.id, user_id=outsider_user_id
        )
        assert participant is not None

        session.add(invitation)
        await session.refresh(invitation)
        assert invitation.usage_count == usages_before + 1

    user_room_listener.assert_next_event(
        expected_name="join-community",
        expected_data={"id": community.id, **community_data},
    )
    user_room_listener.assert_no_more_events()

    participant_list_listener.assert_next_event(
        expected_name="create-participant",
        expected_data={
            "community_id": community.id,
            "user_id": outsider_user_id,
            "created_at": participant.created_at,
            "is_owner": False,
        },
    )
    participant_list_listener.assert_no_more_events()


async def test_community_joining_invitation_not_found(
    tmexio_outsider_client: TMEXIOTestClient,
    deleted_invitation_code: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            "join-community", code=deleted_invitation_code
        ),
        expected_code=404,
        expected_data="Invitation not found",
    )
    tmexio_outsider_client.assert_no_more_events()


async def test_community_joining_already_joined(
    tmexio_actor_client: TMEXIOTestClient,
    invitation: Invitation,
) -> None:
    assert_ack(
        await tmexio_actor_client.emit("join-community", code=invitation.token),
        expected_code=409,
        expected_data="Already joined",
    )
    tmexio_actor_client.assert_no_more_events()
