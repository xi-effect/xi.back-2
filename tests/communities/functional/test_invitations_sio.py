from datetime import datetime

import pytest
from starlette import status

from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.communities.factories import InvitationInputFactory

pytestmark = pytest.mark.anyio


async def test_invitations_listing(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    invitations_data: list[AnyJSON],
) -> None:
    assert_ack(
        await tmexio_owner_client.emit("list-invitations", community_id=community.id),
        expected_data=invitations_data,
    )
    tmexio_owner_client.assert_no_more_events()


async def test_invitations_listing_invalid_invitation_not_shown(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    invalid_invitation: Invitation,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit("list-invitations", community_id=community.id),
        expected_data=[],
    )
    tmexio_owner_client.assert_no_more_events()


async def test_invitations_listing_empty_list(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit("list-invitations", community_id=community.id),
        expected_data=[],
    )
    tmexio_owner_client.assert_no_more_events()


async def test_invitation_creation(
    active_session: ActiveSession,
    community: Community,
    owner_user_id: int,
    tmexio_owner_client: TMEXIOTestClient,
) -> None:
    invitation_input_data = InvitationInputFactory.build_json()

    invitation_id: int = assert_ack(
        await tmexio_owner_client.emit(
            "create-invitation",
            community_id=community.id,
            data=invitation_input_data,
        ),
        expected_data={
            **invitation_input_data,
            "id": int,
            "token": str,
            "usage_count": 0,
            "created_at": datetime,
            "creator_id": owner_user_id,
        },
    )[1]["id"]
    tmexio_owner_client.assert_no_more_events()

    async with active_session():
        invitation = await Invitation.find_first_by_id(invitation_id)
        assert invitation is not None
        await invitation.delete()


async def test_invitation_creation_quantity_exceed(
    mock_stack: MockStack,
    active_session: ActiveSession,
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
) -> None:
    mock_stack.enter_mock(Invitation, "max_count", property_value=0)
    assert_ack(
        await tmexio_owner_client.emit(
            "create-invitation",
            community_id=community.id,
            data=InvitationInputFactory.build_json(),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_data="Quantity exceeded",
    )
    tmexio_owner_client.assert_no_more_events()


async def test_invitation_deleting(
    active_session: ActiveSession,
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    invitation: Invitation,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "delete-invitation",
            community_id=community.id,
            invitation_id=invitation.id,
        ),
        expected_code=204,
    )

    async with active_session():
        assert (await Invitation.find_first_by_id(invitation.id)) is None


async def test_invitation_deleting_invitation_not_found(
    active_session: ActiveSession,
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    deleted_invitation_id: int,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "delete-invitation",
            community_id=community.id,
            invitation_id=deleted_invitation_id,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Invitation not found",
    )


@pytest.mark.parametrize(
    "event_name",
    [
        pytest.param("list-invitations", id="list"),
        pytest.param("create-invitation", id="create"),
        pytest.param("delete-invitation", id="delete"),
    ],
)
async def test_invitations_requesting_community_not_found(
    deleted_community_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=deleted_community_id,
            invitation_id=0,
            data={},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Community not found",
    )


@pytest.mark.parametrize(
    "event_name",
    [
        pytest.param("list-invitations", id="list"),
        pytest.param("create-invitation", id="create"),
        pytest.param("delete-invitation", id="delete"),
    ],
)
async def test_invitations_requesting_not_sufficient_permissions(
    community: Community,
    tmexio_participant_client: TMEXIOTestClient,
    invitation: Invitation,
    event_name: str,
) -> None:
    # TODO 403 should be before 404, so invitation should not be needed
    #   https://github.com/niqzart/tmexio/issues/4
    assert_ack(
        await tmexio_participant_client.emit(
            event_name,
            community_id=community.id,
            invitation_id=invitation.id,
            data={},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="Not sufficient permissions",
    )


@pytest.mark.parametrize(
    "event_name",
    [
        pytest.param("list-invitations", id="list"),
        pytest.param("create-invitation", id="create"),
        pytest.param("delete-invitation", id="delete"),
    ],
)
async def test_invitations_requesting_no_access_to_community(
    community: Community,
    tmexio_outsider_client: TMEXIOTestClient,
    invitation: Invitation,
    event_name: str,
) -> None:
    # TODO 403 should be before 404, so invitation should not be needed
    #   https://github.com/niqzart/tmexio/issues/4
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=community.id,
            invitation_id=invitation.id,
            data={},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="No access to community",
    )
