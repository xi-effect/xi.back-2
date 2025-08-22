from pydantic_marshals.base import CompositeMarshalModel
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.responses import SelfReferenceResponses
from app.tutors.dependencies.invitations_dep import InvitationByCode
from app.tutors.models.tutorships_db import Tutorship

router = APIRouterExt(tags=["student invitations"])


class InvitationPreviewSchema(CompositeMarshalModel):
    tutor_id: int


@router.get(
    "/roles/student/invitations/{code}/preview/",
    responses=SelfReferenceResponses.responses(),
    response_model=InvitationPreviewSchema.build_marshal(),
    summary="Preview a tutor invitation by code",
)
async def preview_invitation(
    auth_data: AuthorizationData,
    invitation: InvitationByCode,
) -> InvitationPreviewSchema:
    if invitation.tutor_id == auth_data.user_id:
        raise SelfReferenceResponses.TARGET_IS_THE_SOURCE

    return InvitationPreviewSchema(tutor_id=invitation.tutor_id)


@router.post(
    "/roles/student/invitations/{code}/usages/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=SelfReferenceResponses.responses(),
    summary="Accept a tutor invitation by code for the current user",
)
async def accept_invitation(
    auth_data: AuthorizationData,
    invitation: InvitationByCode,
) -> None:
    if invitation.tutor_id == auth_data.user_id:
        raise SelfReferenceResponses.TARGET_IS_THE_SOURCE

    invitation.usage_count += 1
    await Tutorship.create(
        tutor_id=invitation.tutor_id,
        student_id=auth_data.user_id,
    )
