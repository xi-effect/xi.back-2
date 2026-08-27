from collections.abc import Sequence
from typing import Annotated

from fastapi import Query

from app.autocomplete.dependencies.tags_dep import SubjectTagByID
from app.autocomplete.models.tags_db import SubjectTag
from app.common.fastapi_ext import APIRouterExt

# TODO remove after xi.tutor switches to the /tag-kinds/subject/ URLs
router = APIRouterExt(tags=["subjects"])


@router.get(
    "/subjects/autocomplete-suggestions/",
    response_model=list[SubjectTag.ResponseSchema],
    summary="Use `GET /api/protected/autocomplete-service/tag-kinds/subject/autocomplete-suggestions/` instead",
    deprecated=True,
)
async def autocomplete_subject(
    search: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(gt=0, le=20)] = 10,
) -> Sequence[SubjectTag]:  # pragma: no cover
    return await SubjectTag.find_for_autocomplete(
        search=search,
        limit=limit,
    )


@router.get(
    "/subjects/{tag_id}/",
    response_model=SubjectTag.ResponseSchema,
    summary="Use `GET /api/protected/autocomplete-service/tag-kinds/subject/tags/{tag_id}/` instead",
    deprecated=True,
)
async def retrieve_subject(
    subject_tag: SubjectTagByID,
) -> SubjectTag:  # pragma: no cover
    return subject_tag
