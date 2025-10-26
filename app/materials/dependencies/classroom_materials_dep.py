from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import with_responses
from app.materials.dependencies.materials_dep import (
    MaterialResponses,
    MyMaterialResponses,
)
from app.materials.models.materials_db import ClassroomMaterial, MaterialAccessMode


@with_responses(MaterialResponses)
async def get_classroom_material_by_id(
    material_id: Annotated[int, Path()],
) -> ClassroomMaterial:
    classroom_material = await ClassroomMaterial.find_first_by_id(material_id)
    if classroom_material is None:
        raise MaterialResponses.MATERIAL_NOT_FOUND
    return classroom_material


ClassroomMaterialByID = Annotated[
    ClassroomMaterial, Depends(get_classroom_material_by_id)
]


@with_responses(MyMaterialResponses)
async def get_my_classroom_material_by_ids(
    classroom_material: ClassroomMaterialByID,
    classroom_id: Annotated[int, Path()],
) -> ClassroomMaterial:
    if classroom_material.classroom_id != classroom_id:
        raise MyMaterialResponses.MATERIAL_ACCESS_DENIED
    return classroom_material


MyClassroomMaterialByIDs = Annotated[
    ClassroomMaterial, Depends(get_my_classroom_material_by_ids)
]


@with_responses(MyMaterialResponses)
async def get_my_student_classroom_material_by_ids(
    classroom_material: MyClassroomMaterialByIDs,
) -> ClassroomMaterial:
    if classroom_material.student_access_mode is MaterialAccessMode.NO_ACCESS:
        raise MyMaterialResponses.MATERIAL_ACCESS_DENIED
    return classroom_material


MyStudentClassroomMaterialByIDs = Annotated[
    ClassroomMaterial, Depends(get_my_student_classroom_material_by_ids)
]
