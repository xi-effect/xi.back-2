import pytest
from fastapi import HTTPException

from app.common.dependencies.authorization_dep import construct_proxy_auth_data
from app.tutors.dependencies.invitations_dep import (
    InvitationResponsesError,
    get_invitation_by_id,
)
from app.tutors.routes.invitations_rst import (
    create_invitation,
    delete_invitation,
    list_invitations,
)
from tests.common.active_session import ActiveSession

pytestmark = pytest.mark.anyio

TEST_USER_ID = "1"
TEST_USERNAME = "a"
TEST_OTHER_USER_ID = "2"
TEST_OTHER_USERNAME = "b"
FIRST_SESSION_ID = "1"
SECOND_SESSION_ID = "2"
THIRD_SESSION_ID = "3"


# tests
async def test_create_tutor_invitation_rst(active_session: ActiveSession) -> None:
    async with active_session():
        response = await create_invitation(
            auth=construct_proxy_auth_data(
                session_id_token=FIRST_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )
        assert response.id == 1, "Invitation has done incorrect"


async def test_delete_tutor_invitation_rst(active_session: ActiveSession) -> None:
    async with active_session():
        invitation = await create_invitation(
            auth=construct_proxy_auth_data(
                session_id_token=FIRST_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )

    async with active_session():
        await delete_invitation(
            invitation,
            auth=construct_proxy_auth_data(
                session_id_token=SECOND_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            ),
        )
        invitations = await list_invitations(
            auth=construct_proxy_auth_data(
                session_id_token=THIRD_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )

        returned_ids = {inv.id for inv in invitations}
        assert (
            invitation.id not in returned_ids
        ), f"Invitation with id: {invitation.id} wasn't deleted"


async def test_delete_invitation_from_different_account_tutor_invitation_rst(
    active_session: ActiveSession,
) -> None:
    async with active_session():
        invitation = await create_invitation(
            auth=construct_proxy_auth_data(
                session_id_token=FIRST_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )
    async with active_session():
        exc_info: pytest.ExceptionInfo[HTTPException]
        with pytest.raises(HTTPException, match="Forbidden") as exc_info:
            await delete_invitation(
                invitation,
                auth=construct_proxy_auth_data(
                    session_id_token=SECOND_SESSION_ID,
                    user_id_token=TEST_OTHER_USER_ID,
                    username_token=TEST_OTHER_USERNAME,
                ),
            )
        assert isinstance(exc_info.value, HTTPException), "HTTPException was expected"
        assert (
            exc_info.value.status_code == 403
        ), f"403 was expected, but received: {exc_info.value.status_code}"


async def test_list_tutor_invitations_rst(active_session: ActiveSession) -> None:
    async with active_session():
        invitation1 = await create_invitation(
            auth=construct_proxy_auth_data(
                session_id_token=FIRST_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )
        invitation2 = await create_invitation(
            auth=construct_proxy_auth_data(
                session_id_token=SECOND_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )
        invitations = await list_invitations(
            auth=construct_proxy_auth_data(
                session_id_token=THIRD_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )

        returned_ids = {inv.id for inv in invitations}

        assert (
            invitation1.id in returned_ids
        ), f"Invitation {invitation1.id} not found in list"
        assert (
            invitation2.id in returned_ids
        ), f"Invitation {invitation2.id} not found in list"


async def test_get_tutor_invitations_rst(active_session: ActiveSession) -> None:
    async with active_session():
        invitation = await create_invitation(
            auth=construct_proxy_auth_data(
                session_id_token=FIRST_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )
        found_invitation = await get_invitation_by_id(invitation.id)
        assert invitation is found_invitation


async def test_get_not_exists_tutor_invitations_rst(
    active_session: ActiveSession,
) -> None:
    async with active_session():
        invitation = await create_invitation(
            auth=construct_proxy_auth_data(
                session_id_token=FIRST_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            )
        )
        await delete_invitation(
            invitation,
            auth=construct_proxy_auth_data(
                session_id_token=SECOND_SESSION_ID,
                user_id_token=TEST_USER_ID,
                username_token=TEST_USERNAME,
            ),
        )
        exc_info: pytest.ExceptionInfo[InvitationResponsesError]
        with pytest.raises(InvitationResponsesError) as exc_info:
            await get_invitation_by_id(invitation.id)
        assert exc_info.value.message == "Invitation not found", "Error wasn't raised"
