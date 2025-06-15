from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.tutors.models.invitations_db import Invitation


class InvitationResponses(Responses):
    INVITATION_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Invitation not found"


@with_responses(InvitationResponses)
async def get_invitation_by_id(invitation_id: Annotated[int, Path()]) -> Invitation:
    invitation = await Invitation.find_first_by_id(invitation_id)
    if invitation is None:
        raise InvitationResponses.INVITATION_NOT_FOUND
    return invitation


InvitationById = Annotated[Invitation, Depends(get_invitation_by_id)]


class MyInvitationResponses(Responses):
    INVITATION_ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Invitation access denied"


@with_responses(MyInvitationResponses)
async def get_my_invitation_by_id(
    invitation: InvitationById, auth_data: AuthorizationData
) -> Invitation:
    if invitation.tutor_id != auth_data.user_id:
        raise MyInvitationResponses.INVITATION_ACCESS_DENIED
    return invitation


MyInvitationById = Annotated[Invitation, Depends(get_my_invitation_by_id)]
