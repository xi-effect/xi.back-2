import pytest
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from app.communities.models.participants_db import Participant
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_retrieving_community_by_invitation_code_authorized(
    authorized_client: TestClient,
    community_data: AnyJSON,
    community: Community,
    invitation: Invitation,
) -> None:
    assert_response(
        authorized_client.get(
            f"/api/public/community-service/invitations/by-code/{invitation.token}/community/"
        ),
        expected_json={
            "community": {**community_data, "id": community.id},
            "is_authorized": True,
            "has_already_joined": False,
        },
    )


async def test_retrieving_community_by_invitation_code_unauthorized(
    client: TestClient,
    community_data: AnyJSON,
    community: Community,
    invitation: Invitation,
) -> None:
    assert_response(
        client.get(
            f"/api/public/community-service/invitations/by-code/{invitation.token}/community/"
        ),
        expected_json={
            "community": {**community_data, "id": community.id},
            "is_authorized": False,
            "has_already_joined": False,
        },
    )


async def test_retrieving_community_by_invitation_code_already_joined(
    client: TestClient,
    community_data: AnyJSON,
    community: Community,
    participant_proxy_auth_data: ProxyAuthData,
    participant: Participant,
    invitation: Invitation,
) -> None:
    assert_response(
        client.get(
            f"/api/public/community-service/invitations/by-code/{invitation.token}/community/",
            headers=participant_proxy_auth_data.as_headers,
        ),
        expected_json={
            "community": {**community_data, "id": community.id},
            "is_authorized": True,
            "has_already_joined": True,
        },
    )


async def test_retrieving_community_by_invitation_code_invitation_not_found(
    client: TestClient, deleted_invitation: Invitation
) -> None:
    assert_response(
        client.get(
            f"/api/public/community-service/invitations/by-code/{deleted_invitation.token}/community/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invitation not found"},
    )


async def test_retrieving_community_by_invitation_code_invalid_invitation(
    client: TestClient, invalid_invitation: Invitation
) -> None:
    assert_response(
        client.get(
            f"/api/public/community-service/invitations/by-code/{invalid_invitation.token}/community/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invitation not found"},
    )
