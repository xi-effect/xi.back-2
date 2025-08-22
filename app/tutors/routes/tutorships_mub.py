from collections.abc import Sequence
from typing import Annotated

from fastapi import Path
from pydantic import AwareDatetime, Field
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.responses import SelfReferenceResponses
from app.tutors.dependencies.tutorships_dep import TutorshipByIDs
from app.tutors.models.tutorships_db import Tutorship

router = APIRouterExt(tags=["tutorships mub"])


@router.get(
    path="/tutors/{tutor_id}/students/",
    response_model=list[Tutorship.TutorResponseSchema],
    summary="List paginated tutorships by tutor id",
)
async def list_tutor_tutorships(
    tutor_id: int,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Sequence[Tutorship]:
    return await Tutorship.find_paginated_by_tutor_id(
        tutor_id=tutor_id,
        created_before=created_before,
        limit=limit,
    )


@router.get(
    path="/students/{student_id}/tutors/",
    response_model=list[Tutorship.StudentResponseSchema],
    summary="List paginated tutorships by student id",
)
async def list_student_tutorships(
    student_id: int,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Sequence[Tutorship]:
    return await Tutorship.find_paginated_by_student_id(
        student_id=student_id,
        created_before=created_before,
        limit=limit,
    )


class ExistingTutorshipResponses(Responses):
    TUTORSHIP_ALREADY_EXISTS = (
        status.HTTP_409_CONFLICT,
        "Tutorship already exists",
    )


@router.post(
    path="/tutors/{tutor_id}/students/{student_id}/",
    status_code=status.HTTP_201_CREATED,
    responses=Responses.chain(ExistingTutorshipResponses, SelfReferenceResponses),
    response_model=Tutorship.ResponseSchema,
    summary="Create a new tutorship between a tutor & student by ids",
)
async def create_tutorship(
    tutor_id: Annotated[int, Path()],
    student_id: Annotated[int, Path()],
) -> Tutorship:
    if tutor_id == student_id:
        raise SelfReferenceResponses.TARGET_IS_THE_SOURCE

    if (
        await Tutorship.find_first_by_kwargs(
            tutor_id=tutor_id,
            student_id=student_id,
        )
        is not None
    ):
        raise ExistingTutorshipResponses.TUTORSHIP_ALREADY_EXISTS

    return await Tutorship.create(
        tutor_id=tutor_id,
        student_id=student_id,
    )


@router.get(
    path="/tutors/{tutor_id}/students/{student_id}/",
    response_model=Tutorship.ResponseSchema,
    summary="Retrieve a tutorship by ids",
)
async def retrieve_tutorship(tutorship: TutorshipByIDs) -> Tutorship:
    return tutorship


@router.delete(
    path="/tutors/{tutor_id}/students/{student_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tutorship by ids",
)
async def delete_tutorship(tutorship: TutorshipByIDs) -> None:
    await tutorship.delete()
