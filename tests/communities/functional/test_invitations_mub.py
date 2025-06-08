import pytest
from starlette import status
from starlette.testclient import TestClient

from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON
from tests.communities.factories import InvitationMUBInputFactory

pytestmark = pytest.mark.anyio


async def test_invitations_listing(
    mub_client: TestClient,
    community: Community,
    invitations_data: list[AnyJSON],
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/communities/{community.id}/invitations/",
        ),
        expected_json=invitations_data,
    )


async def test_invitations_listing_invalid_invitations_shown(
    mub_client: TestClient,
    community: Community,
    invalid_invitation: Invitation,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/communities/{community.id}/invitations/",
        ),
        expected_json=[
            Invitation.ResponseSchema.model_validate(
                invalid_invitation, from_attributes=True
            ).model_dump(mode="json")
        ],
    )


async def test_invitations_listing_empty_list(
    mub_client: TestClient,
    community: Community,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/communities/{community.id}/invitations/",
        ),
        expected_json=[],
    )


async def test_invitation_creation(  # TODO community_not_finding
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
) -> None:
    invitation_input_data = InvitationMUBInputFactory.build_json()

    invitation_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/invitations/",
            json=invitation_input_data,
        ),
        expected_code=201,
        expected_json={
            **invitation_input_data,
            "id": int,
        },
    ).json()["id"]

    async with active_session():
        invitation = await Invitation.find_first_by_id(invitation_id)
        assert invitation is not None
        await invitation.delete()


async def test_invitation_creation_quantity_exceed(
    mock_stack: MockStack,
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
) -> None:
    mock_stack.enter_mock(Invitation, "max_count", property_value=0)
    assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/invitations/",
            json=InvitationMUBInputFactory.build_json(),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Quantity exceeded"},
    )


@pytest.mark.parametrize(
    "method", [pytest.param("GET", id="list"), pytest.param("POST", id="create")]
)
async def test_invitations_requesting_community_not_found(
    mub_client: TestClient,
    deleted_community_id: int,
    method: str,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/communities/{deleted_community_id}/invitations/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Community not found"},
    )


async def test_invitation_retrieving(
    mub_client: TestClient,
    invitation: Invitation,
    invitation_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/invitations/{invitation.id}/"),
        expected_json=invitation_data,
    )


async def test_invitation_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    invitation: Invitation,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/invitations/{invitation.id}/")
    )

    async with active_session():
        assert (await Invitation.find_first_by_id(invitation.id)) is None


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("GET", id="get"),
        pytest.param("DELETE", id="delete"),
    ],
)
async def test_invitation_not_finding(
    mub_client: TestClient,
    active_session: ActiveSession,
    deleted_invitation_id: int,
    method: str,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/invitations/{deleted_invitation_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invitation not found"},
    )
