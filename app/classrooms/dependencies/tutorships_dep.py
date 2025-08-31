from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.classrooms.models.tutorships_db import Tutorship
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses


class TutorshipResponses(Responses):
    TUTORSHIP_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Tutorship not found"


async def get_tutorship_by_ids(tutor_id: int, student_id: int) -> Tutorship:
    tutorship = await Tutorship.find_first_by_kwargs(
        tutor_id=tutor_id,
        student_id=student_id,
    )
    if tutorship is None:
        raise TutorshipResponses.TUTORSHIP_NOT_FOUND
    return tutorship


@with_responses(TutorshipResponses)
async def get_mub_tutorship_by_ids(
    tutor_id: Annotated[int, Path()],
    student_id: Annotated[int, Path()],
) -> Tutorship:
    return await get_tutorship_by_ids(
        tutor_id=tutor_id,
        student_id=student_id,
    )


TutorshipByIDs = Annotated[Tutorship, Depends(get_mub_tutorship_by_ids)]


@with_responses(TutorshipResponses)
async def get_my_tutor_tutorship_by_ids(
    auth_data: AuthorizationData,
    student_id: Annotated[int, Path()],
) -> Tutorship:
    return await get_tutorship_by_ids(
        tutor_id=auth_data.user_id,
        student_id=student_id,
    )


MyTutorTutorshipByIDs = Annotated[Tutorship, Depends(get_my_tutor_tutorship_by_ids)]


@with_responses(TutorshipResponses)
async def get_my_student_tutorship_by_ids(
    auth_data: AuthorizationData,
    tutor_id: Annotated[int, Path()],
) -> Tutorship:
    return await get_tutorship_by_ids(
        tutor_id=tutor_id,
        student_id=auth_data.user_id,
    )


MyStudentTutorshipByIDs = Annotated[Tutorship, Depends(get_my_student_tutorship_by_ids)]
