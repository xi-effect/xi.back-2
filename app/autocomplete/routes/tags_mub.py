from collections.abc import Sequence

from starlette import status

from app.autocomplete.dependencies.tags_dep import (
    ExistingTagResponses,
    TagByKindAndID,
    TagClassByKind,
)
from app.autocomplete.models.tags_db import AnyTag, Tag
from app.common.fastapi_ext import APIRouterExt

router = APIRouterExt(tags=["tags mub"])


@router.get(
    "/tag-kinds/{tag_kind}/tags/",
    response_model=list[Tag.ResponseMUBSchema],
    summary="List paginated tags",
)
async def list_tags(
    tag_class: TagClassByKind,
    offset: int = 0,
    limit: int = 10,
    tutor_id: int | None = None,
) -> Sequence[AnyTag]:
    return await tag_class.find_paginated_by_tutor_id(
        tutor_id=tutor_id,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/tag-kinds/{tag_kind}/tags/",
    status_code=status.HTTP_201_CREATED,
    response_model=Tag.ResponseMUBSchema,
    responses=ExistingTagResponses.responses(),
    summary="Create a new tag",
)
async def create_tag(tag_class: TagClassByKind, data: Tag.InputMUBSchema) -> AnyTag:
    if await tag_class.is_present_by_name(data.name, data.tutor_id):
        raise ExistingTagResponses.TAG_ALREADY_EXISTS
    return await tag_class.create(**data.model_dump())


@router.patch(
    "/tag-kinds/{tag_kind}/tags/{tag_id}/",
    response_model=Tag.ResponseMUBSchema,
    summary="Update any tag by id",
)
async def patch_tag(
    tag: TagByKindAndID,
    data: Tag.PatchMUBSchema,
) -> AnyTag:
    tag.update(**data.model_dump(exclude_defaults=True))
    return tag


@router.delete(
    "/tag-kinds/{tag_kind}/tags/{tag_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any tag by id",
)
async def delete_tag(tag: TagByKindAndID) -> None:
    await tag.delete()
