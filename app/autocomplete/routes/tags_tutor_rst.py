from pydantic_marshals.base import PatchDefault
from starlette import status

from app.autocomplete.dependencies.tags_dep import (
    ExistingTagResponses,
    MyTagByKindAndID,
    TagClassByKind,
)
from app.autocomplete.models.tags_db import AnyTag, Tag
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.responses import LimitedListResponses

router = APIRouterExt(tags=["tutor tags"])


@router.post(
    "/roles/tutor/tag-kinds/{tag_kind}/tags/",
    status_code=status.HTTP_201_CREATED,
    response_model=Tag.ResponseSchema,
    responses=Responses.chain(ExistingTagResponses, LimitedListResponses),
    summary="Create a new tag for the current user",
)
async def create_tag(
    auth_data: AuthorizationData,
    tag_class: TagClassByKind,
    data: Tag.InputSchema,
) -> AnyTag:
    if await tag_class.is_present_by_name(data.name, auth_data.user_id):
        raise ExistingTagResponses.TAG_ALREADY_EXISTS
    if await tag_class.is_limit_per_tutor_reached(tutor_id=auth_data.user_id):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    return await tag_class.create(**data.model_dump(), tutor_id=auth_data.user_id)


@router.patch(
    "/roles/tutor/tag-kinds/{tag_kind}/tags/{tag_id}/",
    response_model=Tag.ResponseSchema,
    responses=ExistingTagResponses.responses(),
    summary="Update tag by id",
)
async def patch_tag(
    tag_class: TagClassByKind,
    tag: MyTagByKindAndID,
    data: Tag.PatchSchema,
) -> AnyTag:
    if (
        data.name is not PatchDefault
        and data.name != tag.name
        and await tag_class.is_present_by_name(data.name, tag.tutor_id)
    ):
        raise ExistingTagResponses.TAG_ALREADY_EXISTS
    tag.update(**data.model_dump(exclude_defaults=True))
    return tag


@router.delete(
    "/roles/tutor/tag-kinds/{tag_kind}/tags/{tag_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag by id",
)
async def delete_tag(tag: MyTagByKindAndID) -> None:
    await tag.delete()
