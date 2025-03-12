from typing import Annotated, Any

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.tutors.models.invitations_db import Invitation


class InvitationResponses(Responses):
    INVITATION_NOT_FOUND = 404, "Invitation not found"


class InvitationResponsesError(RuntimeError):
    def __init__(self, *args: Any) -> None:
        self.message: str = "Invitation not found"

    def __str__(self) -> str:
        return self.message


@with_responses(InvitationResponses)
async def get_invitation_by_id(invitation_id: Annotated[int, Path()]) -> Invitation:
    invitation: Invitation | None = await Invitation.find_first_by_id(invitation_id)
    if invitation is None:
        raise InvitationResponsesError
    return invitation


InvitationById = Annotated[Invitation, Depends(get_invitation_by_id)]
