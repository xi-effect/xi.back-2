from collections.abc import Sequence
from typing import Annotated

from pydantic import AwareDatetime, Field
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.tutors.dependencies.tutorships_dep import TutorTutorshipByIDs
from app.tutors.models.tutorships_db import Tutorship

router = APIRouterExt(tags=["tutor students"])


@router.get(
    path="/roles/tutor/students/",
    response_model=list[Tutorship.TutorResponseSchema],
    summary="List all tutor students for the current user",
)
async def list_students(
    auth_data: AuthorizationData,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Sequence[Tutorship]:
    return await Tutorship.find_paginated_by_tutor_id(
        tutor_id=auth_data.user_id,
        created_before=created_before,
        limit=limit,
    )


@router.get(
    path="/roles/tutor/students/{student_id}/",
    response_model=Tutorship.ResponseSchema,
    summary="Retrieve a tutor student from the current user by id",
)
async def retrieve_student(tutorship: TutorTutorshipByIDs) -> Tutorship:
    return tutorship


@router.delete(
    path="/roles/tutor/students/{student_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tutor student from the current user by id",
)
async def delete_student(tutorship: TutorTutorshipByIDs) -> None:
    await tutorship.delete()
