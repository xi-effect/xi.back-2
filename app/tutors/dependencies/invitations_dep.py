from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.tutors.models.invitations_db import IndividualInvitation, Invitation


class InvitationResponses(Responses):
    INVITATION_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Invitation not found"


@with_responses(InvitationResponses)
async def get_invitation_by_code(code: Annotated[str, Path()]) -> IndividualInvitation:
    # TODO group invitations
    invitation = await IndividualInvitation.find_first_by_kwargs(code=code)
    if invitation is None:
        raise InvitationResponses.INVITATION_NOT_FOUND
    return invitation


InvitationByCode = Annotated[IndividualInvitation, Depends(get_invitation_by_code)]


@with_responses(InvitationResponses)
async def get_individual_invitation_by_id(
    invitation_id: Annotated[int, Path()],
) -> IndividualInvitation:
    individual_invitation = await IndividualInvitation.find_first_by_id(invitation_id)
    if individual_invitation is None:
        raise InvitationResponses.INVITATION_NOT_FOUND
    return individual_invitation


IndividualInvitationByID = Annotated[
    IndividualInvitation, Depends(get_individual_invitation_by_id)
]


class MyInvitationResponses(Responses):
    INVITATION_ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Invitation access denied"


@with_responses(MyInvitationResponses)
async def get_my_individual_invitation_by_id(
    individual_invitation: IndividualInvitationByID, auth_data: AuthorizationData
) -> IndividualInvitation:
    if individual_invitation.tutor_id != auth_data.user_id:
        raise MyInvitationResponses.INVITATION_ACCESS_DENIED
    return individual_invitation


MyIndividualInvitationByID = Annotated[
    Invitation, Depends(get_my_individual_invitation_by_id)
]
