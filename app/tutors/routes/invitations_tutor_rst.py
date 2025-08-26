from collections.abc import Sequence

from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.responses import LimitedListResponses
from app.tutors.dependencies.invitations_dep import MyIndividualInvitationByID
from app.tutors.models.invitations_db import IndividualInvitation

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


@router.delete(
    "/roles/tutor/individual-invitations/{invitation_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete individual tutor invitation from current user by id",
)
async def delete_individual_invitation(
    individual_invitation: MyIndividualInvitationByID,
) -> None:
    await individual_invitation.delete()
