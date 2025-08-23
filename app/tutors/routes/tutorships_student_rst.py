from typing import Annotated

from pydantic import AwareDatetime, Field
from pydantic_marshals.base import CompositeMarshalModel

from app.common.config_bdg import users_internal_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.users_sch import UserProfileSchema
from app.tutors.dependencies.tutorships_dep import MyStudentTutorshipByIDs
from app.tutors.models.tutorships_db import Tutorship

router = APIRouterExt(tags=["student tutors"])


class StudentTutorSchema(CompositeMarshalModel):
    tutorship: Annotated[Tutorship, Tutorship.StudentResponseSchema]
    user: UserProfileSchema


@router.get(
    path="/roles/student/tutors/",
    response_model=list[StudentTutorSchema.build_marshal()],  # type: ignore[misc]
    # TODO https://github.com/niqzart/pydantic-marshals/issues/40
    summary="List all student tutors for the current user",
)
async def list_students(
    auth_data: AuthorizationData,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> list[StudentTutorSchema]:
    tutorships = await Tutorship.find_paginated_by_student_id(
        student_id=auth_data.user_id,
        created_before=created_before,
        limit=limit,
    )
    user_id_to_profile = await users_internal_bridge.retrieve_multiple_users(
        user_ids=[tutorship.tutor_id for tutorship in tutorships]
    )
    return [
        StudentTutorSchema(
            tutorship=tutorship,
            user=user_id_to_profile[str(tutorship.tutor_id)],
        )
        for tutorship in tutorships
    ]


@router.get(
    path="/roles/student/tutors/{tutor_id}/",
    summary="Retrieve a student tutor from the current user by id",
)
async def retrieve_tutor(tutorship: MyStudentTutorshipByIDs) -> UserProfileSchema:
    return await users_internal_bridge.retrieve_user(user_id=tutorship.tutor_id)
