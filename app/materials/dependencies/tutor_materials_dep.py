from typing import Annotated

from fastapi import Depends, Path

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import with_responses
from app.materials.dependencies.materials_dep import (
    MaterialResponses,
    MyMaterialResponses,
)
from app.materials.models.materials_db import TutorMaterial


@with_responses(MaterialResponses)
async def get_tutor_material_by_id(
    material_id: Annotated[int, Path()],
) -> TutorMaterial:
    tutor_material = await TutorMaterial.find_first_by_id(material_id)
    if tutor_material is None:
        raise MaterialResponses.MATERIAL_NOT_FOUND
    return tutor_material


TutorMaterialByID = Annotated[TutorMaterial, Depends(get_tutor_material_by_id)]


@with_responses(MyMaterialResponses)
async def get_my_tutor_material_by_id(
    tutor_material: TutorMaterialByID,
    auth_data: AuthorizationData,
) -> TutorMaterial:
    if tutor_material.tutor_id != auth_data.user_id:
        raise MyMaterialResponses.MATERIAL_ACCESS_DENIED
    return tutor_material


MyTutorMaterialByID = Annotated[TutorMaterial, Depends(get_my_tutor_material_by_id)]
