from collections.abc import Sequence

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.content.models.materials_db import (
    NAMED_MATERIAL_ACCESS_KINDS,
    AnyMaterialSearchRequestSchema,
    AnyNamedMaterialResponseSchema,
    Material,
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
