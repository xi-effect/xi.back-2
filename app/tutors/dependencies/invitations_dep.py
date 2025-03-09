from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.tutors.models.tutor_invitations_db import Invitation


class InvitationResponses(Responses):
    INVITATION_NOT_FOUND = 404, "Invitation not found"


@with_responses(InvitationResponses)
async def get_invitation_by_id(invitation_id: Annotated[int, Path()]) -> Invitation:
    invitation = await Invitation.find_first_by_id(invitation_id)
    if invitation is None:
        raise InvitationResponses.INVITATION_NOT_FOUND
    return invitation


InvitationById = Annotated[Invitation, Depends(get_invitation_by_id)]
