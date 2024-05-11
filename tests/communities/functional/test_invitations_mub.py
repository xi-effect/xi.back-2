import pytest
from starlette.testclient import TestClient

from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON
from tests.communities.factories import InvitationFullInputFactory

pytestmark = pytest.mark.anyio


async def test_invitation_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
) -> None:
    invitation_input_data = InvitationFullInputFactory.build_json()

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
            json=InvitationFullInputFactory.build_json(),
        ),
        expected_code=409,
        expected_json={"detail": "Quantity exceeded"},
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
        expected_code=404,
        expected_json={"detail": "Invitation not found"},
    )
