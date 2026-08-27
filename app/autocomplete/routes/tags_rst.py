from collections.abc import Sequence
from typing import Annotated

from fastapi import Query

from app.autocomplete.dependencies.tags_dep import SubjectTagByID
from app.autocomplete.models.tags_db import SubjectTag, Tag
from app.common.fastapi_ext import APIRouterExt

router = APIRouterExt(tags=["tags"])


@router.get(
    "/tag-kinds/subject/autocomplete-suggestions/",
    response_model=list[Tag.ResponseSchema],
    summary="Retrieve tag suggestions for autocomplete",
)
async def autocomplete_tag(
    search: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(gt=0, le=20)] = 10,
) -> Sequence[SubjectTag]:
    return await SubjectTag.find_for_autocomplete(
        search=search,
        limit=limit,
    )


@router.get(
    "/tag-kinds/subject/tags/{tag_id}/",
    response_model=Tag.ResponseSchema,
    summary="Retrieve any tag by id",
)
async def retrieve_tag(tag: SubjectTagByID) -> SubjectTag:
    return tag
