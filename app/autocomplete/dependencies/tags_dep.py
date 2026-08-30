from typing import Annotated, assert_never

from fastapi import Depends, Path
from starlette import status

from app.autocomplete.models.tags_db import AnyTag, GenericTag, SubjectTag
from app.common.fastapi_ext import Responses, with_responses
from app.common.schemas.autocomplete_sch import TagKind


def get_tag_class_by_kind(tag_kind: Annotated[TagKind, Path()]) -> type[AnyTag]:
    match tag_kind:
        case TagKind.SUBJECT:
            return SubjectTag
        case TagKind.GENERIC:
            return GenericTag
        case _:
            assert_never(tag_kind)


TagClassByKind = Annotated[type[AnyTag], Depends(get_tag_class_by_kind)]


class TagResponses(Responses):
    TAG_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Tag not found"


@with_responses(TagResponses)
async def get_tag_by_kind_and_id(
    tag_class: TagClassByKind,
    tag_id: Annotated[int, Path()],
) -> AnyTag:
    tag = await tag_class.find_first_by_id(tag_id)
    if tag is None:
        raise TagResponses.TAG_NOT_FOUND
    return tag


TagByKindAndID = Annotated[AnyTag, Depends(get_tag_by_kind_and_id)]
