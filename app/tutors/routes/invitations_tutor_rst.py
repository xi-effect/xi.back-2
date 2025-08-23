from collections.abc import Sequence

from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.tutors.dependencies.invitations_dep import MyInvitationByID
from app.tutors.models.invitations_db import Invitation

router = APIRouterExt(tags=["tutor invitations"])


@router.get(
    "/roles/tutor/invitations/",
    response_model=list[Invitation.ResponseSchema],
    summary="List all tutor invitations for the current user",
)
async def list_invitations(auth_data: AuthorizationData) -> Sequence[Invitation]:
    return await Invitation.find_all_by_kwargs(
        Invitation.created_at,
        tutor_id=auth_data.user_id,
    )


class InvitationCreationResponses(Responses):
    INVITATION_QUANTITY_EXCEEDED = (
        status.HTTP_409_CONFLICT,
        "Invitation quantity exceeded",
    )


@router.post(
    "/roles/tutor/invitations/",
    status_code=status.HTTP_201_CREATED,
    response_model=Invitation.ResponseSchema,
    responses=InvitationCreationResponses.responses(),
    summary="Create a new tutor invitation for the current user",
)
async def create_invitation(auth_data: AuthorizationData) -> Invitation:
    if (
        await Invitation.count_by_tutor_id(tutor_id=auth_data.user_id)
        >= Invitation.max_count
    ):
        raise InvitationCreationResponses.INVITATION_QUANTITY_EXCEEDED
    return await Invitation.create(tutor_id=auth_data.user_id)


@router.delete(
    "/roles/tutor/invitations/{invitation_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tutor invitation from current user by id",
)
async def delete_invitation(invitation: MyInvitationByID) -> None:
    await invitation.delete()
