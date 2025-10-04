from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.classrooms.dependencies.classrooms_tutor_dep import MyTutorGroupClassroomByID
from app.classrooms.models.invitations_db import (
    AnyInvitation,
    GroupInvitation,
    IndividualInvitation,
    Invitation,
)
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.common.responses import SelfReferenceResponses


class InvitationResponses(Responses):
    INVITATION_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Invitation not found"


@with_responses(InvitationResponses)
async def get_invitation_by_code(code: Annotated[str, Path()]) -> AnyInvitation:
    invitation = await Invitation.find_first_by_kwargs(code=code)
    if invitation is None:
        raise InvitationResponses.INVITATION_NOT_FOUND
    if not isinstance(invitation, AnyInvitation):  # pragma: no cover
        raise TypeError("SQLAlchemy returned an unknown type of Invitation")
    return invitation


InvitationByCode = Annotated[AnyInvitation, Depends(get_invitation_by_code)]


@with_responses(SelfReferenceResponses)
async def get_foreign_invitation_by_code(
    invitation: InvitationByCode, auth_data: AuthorizationData
) -> AnyInvitation:
    if invitation.tutor_id == auth_data.user_id:
        raise SelfReferenceResponses.TARGET_IS_THE_SOURCE
    return invitation


ForeignInvitationByCode = Annotated[
    AnyInvitation, Depends(get_foreign_invitation_by_code)
]


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


@with_responses(InvitationResponses)
async def get_my_group_invitation_by_group_classroom_id(
    group_classroom: MyTutorGroupClassroomByID,
) -> GroupInvitation:
    group_invitation = await GroupInvitation.find_first_by_group_classroom_id(
        group_classroom_id=group_classroom.id,
    )
    if group_invitation is None:
        raise InvitationResponses.INVITATION_NOT_FOUND
    return group_invitation


MyGroupInvitationByGroupClassroomID = Annotated[
    GroupInvitation, Depends(get_my_group_invitation_by_group_classroom_id)
]
