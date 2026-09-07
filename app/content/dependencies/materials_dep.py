from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.content.models.materials_db import Material


class MaterialResponses(Responses):
    MATERIAL_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Material not found"


class MyMaterialResponses(Responses):
    MATERIAL_ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Material access denied"


@with_responses(MaterialResponses)
async def get_material_by_id(material_id: Annotated[UUID, Path()]) -> Material:
    material = await Material.find_first_by_id(material_id)
    if material is None:
        raise MaterialResponses.MATERIAL_NOT_FOUND
    return material


MaterialByID = Annotated[Material, Depends(get_material_by_id)]


@with_responses(MyMaterialResponses)
async def get_my_material_by_id(
    auth_data: AuthorizationData,
    material: MaterialByID,
) -> Material:
    if material.main_ydoc.owner_id != auth_data.user_id:
        raise MyMaterialResponses.MATERIAL_ACCESS_DENIED
    return material


MyMaterialByID = Annotated[Material, Depends(get_my_material_by_id)]
