from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.tutors.models.materials_db import Material


class MaterialResponses(Responses):
    ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Material access denied"
    MATERIAL_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Material not found"


@with_responses(MaterialResponses)
async def get_material_by_id(
    material_id: Annotated[int, Path()], auth_data: AuthorizationData
) -> Material:
    material = await Material.find_first_by_id(material_id)
    if material is None:
        raise MaterialResponses.MATERIAL_NOT_FOUND
    if material.tutor_id != auth_data.user_id:
        raise MaterialResponses.ACCESS_DENIED
    return material


MaterialByID = Annotated[Material, Depends(get_material_by_id)]
