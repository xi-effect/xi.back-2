from collections.abc import Sequence
from typing import Annotated

from fastapi import Query

from app.autocomplete.dependencies.subjects_dep import SubjectByID
from app.autocomplete.models.subjects_db import Subject
from app.common.fastapi_ext import APIRouterExt

router = APIRouterExt(tags=["subjects"])


@router.get(
    "/subjects/autocomplete-suggestions/",
    response_model=list[Subject.ResponseSchema],
    summary="Retrieve subject suggestions for autocomplete",
)
async def autocomplete_subject(
    search: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(gt=0, le=20)] = 10,
) -> Sequence[Subject]:
    return await Subject.find_for_autocomplete(
        search=search,
        limit=limit,
    )


@router.get(
    "/subjects/{subject_id}/",
    response_model=Subject.ResponseSchema,
    summary="Retrieve any subject by id",
)
async def retrieve_subject(subject: SubjectByID) -> Subject:
    return subject
