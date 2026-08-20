from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import with_responses
from app.content.dependencies.materials_dep import (
    MaterialResponses,
    MyMaterialResponses,
)
from app.content.models.materials_db import PersonalMaterial


@with_responses(MaterialResponses)
async def get_personal_material_by_id(
    material_id: Annotated[UUID, Path()],
) -> PersonalMaterial:
    personal_material = await PersonalMaterial.find_first_by_id(material_id)
    if personal_material is None:
        raise MaterialResponses.MATERIAL_NOT_FOUND
    return personal_material


PersonalMaterialByID = Annotated[PersonalMaterial, Depends(get_personal_material_by_id)]


@with_responses(MyMaterialResponses)
async def get_my_personal_material_by_id(
    personal_material: PersonalMaterialByID,
    auth_data: AuthorizationData,
) -> PersonalMaterial:
    if personal_material.tutor_id != auth_data.user_id:
        raise MyMaterialResponses.MATERIAL_ACCESS_DENIED
    return personal_material


MyPersonalMaterialByID = Annotated[
    PersonalMaterial, Depends(get_my_personal_material_by_id)
]
