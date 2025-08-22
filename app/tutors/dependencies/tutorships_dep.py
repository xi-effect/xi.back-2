from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.tutors.models.tutorships_db import Tutorship


class TutorshipResponses(Responses):
    TUTORSHIP_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Tutorship not found"


@with_responses(TutorshipResponses)
async def get_tutorship_by_ids(
    tutor_id: Annotated[int, Path()],
    student_id: Annotated[int, Path()],
) -> Tutorship:
    tutorship = await Tutorship.find_first_by_kwargs(
        tutor_id=tutor_id,
        student_id=student_id,
    )
    if tutorship is None:
        raise TutorshipResponses.TUTORSHIP_NOT_FOUND
    return tutorship


TutorshipByIDs = Annotated[Tutorship, Depends(get_tutorship_by_ids)]
