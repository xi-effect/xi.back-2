from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.autocomplete.models.tags_db import SubjectTag
from app.common.fastapi_ext import Responses, with_responses


class TagResponses(Responses):
    TAG_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Tag not found"


@with_responses(TagResponses)
async def get_subject_tag_by_id(tag_id: Annotated[int, Path()]) -> SubjectTag:
    subject_tag = await SubjectTag.find_first_by_id(tag_id)
    if subject_tag is None:
        raise TagResponses.TAG_NOT_FOUND
    return subject_tag


SubjectTagByID = Annotated[SubjectTag, Depends(get_subject_tag_by_id)]
