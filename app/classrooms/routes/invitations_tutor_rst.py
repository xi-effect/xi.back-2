from collections.abc import Sequence

from fastapi import Response
from starlette import status

from app.classrooms.dependencies.classrooms_tutor_dep import MyTutorGroupClassroomByID
from app.classrooms.dependencies.invitations_dep import MyIndividualInvitationByID
from app.classrooms.models.invitations_db import GroupInvitation, IndividualInvitation
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.responses import LimitedListResponses

router = APIRouterExt(tags=["tutor invitations"])


@router.get(
    "/roles/tutor/individual-invitations/",
    response_model=list[IndividualInvitation.ResponseSchema],
    summary="List all individual tutor invitations for the current user",
)
async def list_individual_invitations(
    auth_data: AuthorizationData,
) -> Sequence[IndividualInvitation]:
    return await IndividualInvitation.find_all_by_kwargs(
        IndividualInvitation.created_at,
        tutor_id=auth_data.user_id,
    )


@router.post(
    "/roles/tutor/individual-invitations/",
    status_code=status.HTTP_201_CREATED,
    response_model=IndividualInvitation.ResponseSchema,
    responses=LimitedListResponses.responses(),
    summary="Create a new individual tutor invitation for the current user",
)
async def create_individual_invitation(
    auth_data: AuthorizationData,
) -> IndividualInvitation:
    if (
        await IndividualInvitation.count_by_tutor_id(tutor_id=auth_data.user_id)
        >= IndividualInvitation.max_count_per_tutor
    ):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    return await IndividualInvitation.create(tutor_id=auth_data.user_id)


@router.post(
    "/roles/tutor/group-classrooms/{classroom_id}/invitation/",
    response_model=GroupInvitation.ResponseSchema,
    summary="Create or retrieve a group tutor invitation for a group classroom by id",
)
async def create_or_retrieve_group_invitation(
    group_classroom: MyTutorGroupClassroomByID,
    response: Response,
) -> GroupInvitation:
    group_invitation = await GroupInvitation.find_first_by_group_classroom_id(
        group_classroom_id=group_classroom.id,
    )
    if group_invitation is None:
        response.status_code = status.HTTP_201_CREATED
        return await GroupInvitation.create(group_classroom=group_classroom)
    return group_invitation


@router.delete(
    "/roles/tutor/individual-invitations/{invitation_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete individual tutor invitation from current user by id",
)
async def delete_individual_invitation(
    individual_invitation: MyIndividualInvitationByID,
) -> None:
    await individual_invitation.delete()
