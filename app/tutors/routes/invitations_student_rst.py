from typing import Annotated, Literal, assert_never

from pydantic import Field
from pydantic_marshals.base import CompositeMarshalModel
from starlette import status

from app.common.config_bdg import users_internal_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.responses import SelfReferenceResponses
from app.common.schemas.users_sch import UserProfileWithIDSchema
from app.tutors.dependencies.invitations_dep import ForeignInvitationByCode
from app.tutors.models.classrooms_db import (
    Classroom,
    ClassroomKind,
    GroupClassroom,
    IndividualClassroom,
    StudentClassroomResponseSchema,
)
from app.tutors.models.enrollments_db import Enrollment
from app.tutors.models.invitations_db import GroupInvitation, IndividualInvitation
from app.tutors.models.tutorships_db import Tutorship

router = APIRouterExt(tags=["student invitations"])


class IndividualInvitationPreviewSchema(CompositeMarshalModel):
    kind: Literal[ClassroomKind.INDIVIDUAL] = ClassroomKind.INDIVIDUAL
    tutor: UserProfileWithIDSchema
    existing_classroom_id: int | None


class GroupInvitationPreviewSchema(CompositeMarshalModel):
    kind: Literal[ClassroomKind.GROUP] = ClassroomKind.GROUP
    tutor: UserProfileWithIDSchema
    classroom: Annotated[GroupClassroom, GroupClassroom.StudentPreviewSchema]
    has_already_joined: bool


InvitationPreviewSchema = Annotated[  # type: ignore[valid-type]
    # TODO https://github.com/niqzart/pydantic-marshals/issues/40
    IndividualInvitationPreviewSchema.build_marshal()
    | GroupInvitationPreviewSchema.build_marshal(),
    Field(discriminator="kind"),
]


async def get_user_profile_with_id(user_id: int) -> UserProfileWithIDSchema:
    tutor_profile = await users_internal_bridge.retrieve_user(user_id=user_id)
    return UserProfileWithIDSchema(
        **tutor_profile.model_dump(),
        user_id=user_id,
    )


async def preview_individual_invitation(
    individual_invitation: IndividualInvitation,
    student_id: int,
) -> IndividualInvitationPreviewSchema:
    existing_classroom_id = await IndividualClassroom.find_classroom_id_by_users(
        tutor_id=individual_invitation.tutor_id,
        student_id=student_id,
    )

    return IndividualInvitationPreviewSchema(
        tutor=await get_user_profile_with_id(user_id=individual_invitation.tutor_id),
        existing_classroom_id=existing_classroom_id,
    )


async def preview_group_invitation(
    group_invitation: GroupInvitation,
    student_id: int,
) -> GroupInvitationPreviewSchema:
    existing_enrollment = await Enrollment.find_first_by_kwargs(
        group_classroom_id=group_invitation.group_classroom_id,
        student_id=student_id,
    )

    return GroupInvitationPreviewSchema(
        tutor=await get_user_profile_with_id(
            user_id=group_invitation.group_classroom.tutor_id
        ),
        classroom=group_invitation.group_classroom,
        has_already_joined=existing_enrollment is not None,
    )


@router.get(
    "/roles/student/invitations/{code}/preview/",
    responses=SelfReferenceResponses.responses(),
    response_model=InvitationPreviewSchema,
    summary="Preview a tutor invitation by code",
)
async def preview_invitation(
    auth_data: AuthorizationData,
    invitation: ForeignInvitationByCode,
) -> IndividualInvitationPreviewSchema | GroupInvitationPreviewSchema:
    match invitation:
        case IndividualInvitation():
            return await preview_individual_invitation(
                individual_invitation=invitation,
                student_id=auth_data.user_id,
            )
        case GroupInvitation():
            return await preview_group_invitation(
                group_invitation=invitation,
                student_id=auth_data.user_id,
            )
        case _:
            assert_never(invitation)


class InvitationAcceptanceResponses(Responses):
    ALREADY_JOINED = status.HTTP_409_CONFLICT, "Already joined"


async def accept_individual_invitation(
    individual_invitation: IndividualInvitation,
    student_id: int,
) -> IndividualClassroom:
    if (
        await IndividualClassroom.find_classroom_id_by_users(
            tutor_id=individual_invitation.tutor_id,
            student_id=student_id,
        )
        is not None
    ):
        raise InvitationAcceptanceResponses.ALREADY_JOINED

    user_id_to_profile = await users_internal_bridge.retrieve_multiple_users(
        user_ids=[individual_invitation.tutor_id, student_id]
    )
    tutor_profile = user_id_to_profile[individual_invitation.tutor_id]
    student_profile = user_id_to_profile[student_id]

    return await IndividualClassroom.create(
        tutor_id=individual_invitation.tutor_id,
        tutor_name=tutor_profile.display_name or tutor_profile.username,
        student_id=student_id,
        student_name=student_profile.display_name or student_profile.username,
    )


async def accept_group_invitation(
    group_invitation: GroupInvitation,
    student_id: int,
) -> GroupClassroom:
    if (
        await Enrollment.find_first_by_kwargs(
            group_classroom_id=group_invitation.group_classroom_id,
            student_id=student_id,
        )
    ) is not None:
        raise InvitationAcceptanceResponses.ALREADY_JOINED

    await Enrollment.create(
        group_classroom_id=group_invitation.group_classroom_id,
        student_id=student_id,
    )

    return group_invitation.group_classroom


@router.post(
    "/roles/student/invitations/{code}/usages/",
    response_model=StudentClassroomResponseSchema,
    responses=Responses.chain(SelfReferenceResponses, InvitationAcceptanceResponses),
    summary="Accept a tutor invitation by code for the current user",
)
async def accept_invitation(
    auth_data: AuthorizationData,
    invitation: ForeignInvitationByCode,
) -> Classroom:
    classroom: Classroom
    match invitation:
        case IndividualInvitation():
            classroom = await accept_individual_invitation(
                individual_invitation=invitation,
                student_id=auth_data.user_id,
            )
        case GroupInvitation():
            classroom = await accept_group_invitation(
                group_invitation=invitation,
                student_id=auth_data.user_id,
            )
        case _:
            assert_never(invitation)

    invitation.usage_count += 1
    await Tutorship.find_or_create(
        tutor_id=invitation.tutor_id,
        student_id=auth_data.user_id,
    )

    return classroom
