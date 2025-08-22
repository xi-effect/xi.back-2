from collections.abc import Sequence
from typing import Annotated

from pydantic import AwareDatetime, Field

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.tutors.dependencies.tutorships_dep import MyStudentTutorshipByIDs
from app.tutors.models.tutorships_db import Tutorship

router = APIRouterExt(tags=["student tutors"])


@router.get(
    path="/roles/student/tutors/",
    response_model=list[Tutorship.StudentResponseSchema],
    summary="List all student tutors for the current user",
)
async def list_students(
    auth_data: AuthorizationData,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Sequence[Tutorship]:
    return await Tutorship.find_paginated_by_student_id(
        student_id=auth_data.user_id,
        created_before=created_before,
        limit=limit,
    )


@router.get(
    path="/roles/student/tutors/{tutor_id}/",
    response_model=Tutorship.ResponseSchema,
    summary="Retrieve a student tutor from the current user by id",
)
async def retrieve_tutor(tutorship: MyStudentTutorshipByIDs) -> Tutorship:
    return tutorship
