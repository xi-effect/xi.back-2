from collections.abc import Sequence

from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.tutors.dependencies.subjects_dep import SubjectById
from app.tutors.models.subjects_db import Subject

router = APIRouterExt(tags=["subjects mub"])


@router.get(
    "/subjects/",
    response_model=list[Subject.ResponseSchema],
    summary="List all subjects",
)
async def list_subjects(
    offset: int = 0,
    limit: int = 10,
    tutor_id: int | None = None,
) -> Sequence[Subject]:
    return await Subject.find_paginated_by_tutor_id(
        tutor_id=tutor_id,
        offset=offset,
        limit=limit,
    )


class SubjectCreationResponses(Responses):
    SUBJECT_ALREADY_EXISTS = status.HTTP_409_CONFLICT, "Subject already exists"


@router.post(
    "/subjects/",
    status_code=status.HTTP_201_CREATED,
    response_model=Subject.ResponseSchema,
    responses=SubjectCreationResponses.responses(),
    summary="Create a new subject",
)
async def create_subject(data: Subject.InputMUBSchema) -> Subject:
    if await Subject.is_present_by_name(data.name, data.tutor_id):
        raise SubjectCreationResponses.SUBJECT_ALREADY_EXISTS
    return await Subject.create(**data.model_dump())


@router.patch(
    "/subjects/{subject_id}/",
    response_model=Subject.ResponseSchema,
    summary="Update any subject by id",
)
async def patch_subject(subject: SubjectById, data: Subject.PatchMUBSchema) -> Subject:
    subject.update(**data.model_dump(exclude_defaults=True))
    return subject


@router.delete(
    "/subjects/{subject_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any subject by id",
)
async def delete_subject(subject: SubjectById) -> None:
    await subject.delete()
