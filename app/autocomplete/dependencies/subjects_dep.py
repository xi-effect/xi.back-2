from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.autocomplete.models.subjects_db import Subject
from app.common.fastapi_ext import Responses, with_responses


class SubjectResponses(Responses):
    SUBJECT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Subject not found"


@with_responses(SubjectResponses)
async def get_subject_by_id(subject_id: Annotated[int, Path()]) -> Subject:
    subject = await Subject.find_first_by_id(subject_id)
    if subject is None:
        raise SubjectResponses.SUBJECT_NOT_FOUND
    return subject


SubjectByID = Annotated[Subject, Depends(get_subject_by_id)]
