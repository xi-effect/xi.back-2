from collections.abc import Sequence
from typing import Annotated

from fastapi import Body
from starlette import status

from app.common.config_bdg import autocomplete_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.autocomplete_sch import TagKind
from app.content.dependencies.materials_dep import MyMaterialByID
from app.content.models.materials_db import (
    NAMED_MATERIAL_ACCESS_KINDS,
    AnyMaterialSearchRequestSchema,
    AnyNamedMaterialResponseSchema,
    Material,
    MaterialTag,
)

router = APIRouterExt(tags=["tutor materials"])


@router.post(
    path="/roles/tutor/materials/searches/",
    response_model=list[AnyNamedMaterialResponseSchema],
    summary="List paginated materials for the current user",
)
async def list_materials(
    auth_data: AuthorizationData,
    data: AnyMaterialSearchRequestSchema,
) -> Sequence[Material]:
    return await Material.find_paginated_by_owner_id(
        owner_id=auth_data.user_id,
        default_allowed_access_kinds=NAMED_MATERIAL_ACCESS_KINDS,
        search_params=data,
    )


class TagResponses(Responses):
    TAG_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Tag not found"


@router.put(
    path="/roles/tutor/materials/{material_id}/tags/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=TagResponses.responses(),
    summary="Set tags for a material by id",
)
async def set_material_tags(
    auth_data: AuthorizationData,
    material: MyMaterialByID,
    tag_ids: Annotated[
        set[int],
        Body(embed=True, max_length=MaterialTag.max_count_per_material),
    ],
) -> None:
    if len(tag_ids) != 0:
        tag_id_to_tag = await autocomplete_bridge.retrieve_multiple_tags(
            kind=TagKind.GENERIC,
            tag_ids=list(tag_ids),
            tutor_id=auth_data.user_id,
        )
        if not tag_ids.issubset(tag_id_to_tag.keys()):
            raise TagResponses.TAG_NOT_FOUND
    await MaterialTag.replace_all_by_material_id(
        material_id=material.id,
        tag_ids=tag_ids,
    )
