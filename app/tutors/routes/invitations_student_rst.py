from pydantic_marshals.base import CompositeMarshalModel
from starlette import status

from app.common.config_bdg import users_internal_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.responses import SelfReferenceResponses
from app.common.schemas.users_sch import UserProfileWithIDSchema
from app.tutors.dependencies.invitations_dep import InvitationByCode
from app.tutors.models.classrooms_db import (
    Classroom,
    IndividualClassroom,
    StudentClassroomResponseSchema,
)
from app.tutors.models.tutorships_db import Tutorship

router = APIRouterExt(tags=["student invitations"])


class InvitationPreviewSchema(CompositeMarshalModel):
    tutor: UserProfileWithIDSchema
    existing_classroom_id: int | None


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

    tutor_profile = await users_internal_bridge.retrieve_user(
        user_id=invitation.tutor_id
    )

    return InvitationPreviewSchema(
        tutor=UserProfileWithIDSchema(
            **tutor_profile.model_dump(),
            user_id=invitation.tutor_id,
        ),
        existing_classroom_id=await IndividualClassroom.find_classroom_id_by_users(
            tutor_id=invitation.tutor_id,
            student_id=auth_data.user_id,
        ),
    )


class InvitationAcceptanceResponses(Responses):
    ALREADY_JOINED = status.HTTP_409_CONFLICT, "Already joined"


@router.post(
    "/roles/student/invitations/{code}/usages/",
    response_model=StudentClassroomResponseSchema,
    responses=Responses.chain(SelfReferenceResponses, InvitationAcceptanceResponses),
    summary="Accept a tutor invitation by code for the current user",
)
async def accept_invitation(
    auth_data: AuthorizationData,
    invitation: InvitationByCode,
) -> Classroom:
    if invitation.tutor_id == auth_data.user_id:
        raise SelfReferenceResponses.TARGET_IS_THE_SOURCE

    if (
        await IndividualClassroom.find_classroom_id_by_users(
            tutor_id=invitation.tutor_id,
            student_id=auth_data.user_id,
        )
        is not None
    ):
        raise InvitationAcceptanceResponses.ALREADY_JOINED

    invitation.usage_count += 1
    await Tutorship.create(
        tutor_id=invitation.tutor_id,
        student_id=auth_data.user_id,
    )

    user_id_to_profile = await users_internal_bridge.retrieve_multiple_users(
        user_ids=[invitation.tutor_id, auth_data.user_id]
    )
    tutor_profile = user_id_to_profile[invitation.tutor_id]
    student_profile = user_id_to_profile[auth_data.user_id]

    return await IndividualClassroom.create(
        tutor_id=invitation.tutor_id,
        tutor_name=tutor_profile.display_name or tutor_profile.username,
        student_id=auth_data.user_id,
        student_name=student_profile.display_name or student_profile.username,
    )
