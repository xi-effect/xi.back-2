from collections.abc import Sequence

from fastapi import HTTPException

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.fastapi_ext import APIRouterExt
from app.tutors.dependencies.invitations_dep import InvitationById
from app.tutors.models.invitations_db import Invitation

router = APIRouterExt(tags=["tutor's invitation"])


@router.post(
    "/invitations/",
    status_code=201,
    response_model=Invitation.ResponseSchema,
    summary="Create the invitation for tutor.",
)
async def create_invitation(auth: ProxyAuthData) -> Invitation:
    # getting user id
    return await Invitation.create(tutor_id=auth.user_id)


@router.delete(
    "/invitations/{invitation_id}",
    status_code=204,
    summary="Delete any invitation by id",
)
async def delete_invitation(invitation: InvitationById, auth: ProxyAuthData) -> None:
    if invitation.tutor_id != auth.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await invitation.delete()


@router.get(
    "/invitations/",
    response_model=list[Invitation.ResponseSchema],
    summary="List invitations for the tutor",
)
async def list_invitations(auth: ProxyAuthData) -> Sequence[Invitation]:
    return await Invitation.find_all_by_kwargs(
        Invitation.created_at,
        tutor_id=auth.user_id,
    )
