from typing import Annotated

from pydantic import AwareDatetime, Field
from pydantic_marshals.base import CompositeMarshalModel
from starlette import status

from app.common.config_bdg import users_internal_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.users_sch import UserProfileSchema
from app.tutors.dependencies.tutorships_dep import MyTutorTutorshipByIDs
from app.tutors.models.tutorships_db import Tutorship

router = APIRouterExt(tags=["tutor students"])


class TutorStudentSchema(CompositeMarshalModel):
    tutorship: Annotated[Tutorship, Tutorship.TutorResponseSchema]
    user: UserProfileSchema


@router.get(
    path="/roles/tutor/students/",
    response_model=list[TutorStudentSchema.build_marshal()],  # type: ignore[misc]
    # TODO https://github.com/niqzart/pydantic-marshals/issues/40
    summary="List all tutor students for the current user",
)
async def list_students(
    auth_data: AuthorizationData,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> list[TutorStudentSchema]:
    tutorships = await Tutorship.find_paginated_by_tutor_id(
        tutor_id=auth_data.user_id,
        created_before=created_before,
        limit=limit,
    )
    user_id_to_profile = await users_internal_bridge.retrieve_multiple_users(
        user_ids=[tutorship.student_id for tutorship in tutorships]
    )
    return [
        TutorStudentSchema(
            tutorship=tutorship,
            user=user_id_to_profile[str(tutorship.student_id)],
        )
        for tutorship in tutorships
    ]


@router.get(
    path="/roles/tutor/students/{student_id}/",
    summary="Retrieve a tutor student for the current user by id",
)
async def retrieve_student(tutorship: MyTutorTutorshipByIDs) -> UserProfileSchema:
    return await users_internal_bridge.retrieve_user(user_id=tutorship.student_id)


@router.delete(
    path="/roles/tutor/students/{student_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tutor student from the current user by id",
)
async def delete_student(tutorship: MyTutorTutorshipByIDs) -> None:
    await tutorship.delete()
