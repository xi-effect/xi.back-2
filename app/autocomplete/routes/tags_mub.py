from collections.abc import Sequence

from starlette import status

from app.autocomplete.dependencies.tags_dep import SubjectTagByID
from app.autocomplete.models.tags_db import SubjectTag, Tag
from app.common.fastapi_ext import APIRouterExt, Responses

router = APIRouterExt(tags=["tags mub"])


@router.get(
    "/tag-kinds/subject/tags/",
    response_model=list[Tag.ResponseMUBSchema],
    summary="List all tags",
)
async def list_tags(
    offset: int = 0,
    limit: int = 10,
    tutor_id: int | None = None,
) -> Sequence[SubjectTag]:
    return await SubjectTag.find_paginated_by_tutor_id(
        tutor_id=tutor_id,
        offset=offset,
        limit=limit,
    )


class ExistingTagResponses(Responses):
    TAG_ALREADY_EXISTS = status.HTTP_409_CONFLICT, "Tag already exists"


@router.post(
    "/tag-kinds/subject/tags/",
    status_code=status.HTTP_201_CREATED,
    response_model=Tag.ResponseMUBSchema,
    responses=ExistingTagResponses.responses(),
    summary="Create a new tag",
)
async def create_tag(data: Tag.InputMUBSchema) -> SubjectTag:
    if await SubjectTag.is_present_by_name(data.name, data.tutor_id):
        raise ExistingTagResponses.TAG_ALREADY_EXISTS
    return await SubjectTag.create(**data.model_dump())


@router.patch(
    "/tag-kinds/subject/tags/{tag_id}/",
    response_model=Tag.ResponseMUBSchema,
    summary="Update any tag by id",
)
async def patch_tag(
    tag: SubjectTagByID,
    data: Tag.PatchMUBSchema,
) -> SubjectTag:
    tag.update(**data.model_dump(exclude_defaults=True))
    return tag


@router.delete(
    "/tag-kinds/subject/tags/{tag_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any tag by id",
)
async def delete_tag(tag: SubjectTagByID) -> None:
    await tag.delete()
