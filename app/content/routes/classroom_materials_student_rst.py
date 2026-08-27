from collections.abc import Sequence
from typing import Annotated, assert_never

from fastapi import Path

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.content_sch import ContentYDocItemSchema, YDocAccessLevel
from app.content.dependencies.classroom_materials_dep import (
    MyClassroomMaterialByIDs,
    MyStudentClassroomMaterialByIDs,
)
from app.content.dependencies.materials_dep import MyMaterialResponses
from app.content.models.materials_db import (
    ClassroomMaterial,
    ClassroomMaterialSearchRequestSchema,
    MaterialAccessMode,
)
from app.content.services import materials_svc

router = APIRouterExt(tags=["student classroom materials"])


@router.post(
    path="/roles/student/classrooms/{classroom_id}/materials/searches/",
    response_model=list[ClassroomMaterial.ResponseSchema],
    summary="List paginated materials in a classroom by id",
)
async def list_classroom_materials(
    classroom_id: Annotated[int, Path()],
    data: ClassroomMaterialSearchRequestSchema,
) -> Sequence[ClassroomMaterial]:
    return await ClassroomMaterial.find_paginated_by_classroom_id(
        classroom_id=classroom_id,
        only_accessible_to_students=True,
        search_params=data,
    )


@router.get(
    path="/roles/student/classrooms/{classroom_id}/materials/{material_id}/",
    response_model=ClassroomMaterial.ResponseSchema,
    summary="Retrieve a classroom material by ids",
)
async def retrieve_classroom_material(
    classroom_material: MyStudentClassroomMaterialByIDs,
) -> ClassroomMaterial:
    return classroom_material


@router.get(
    path="/roles/student/classrooms/{classroom_id}/materials/{material_id}/storage-item/",
    summary="Retrieve a storage item for a classroom material by ids",
)
async def retrieve_classroom_material_storage_item(
    classroom_material: MyClassroomMaterialByIDs,
    auth_data: AuthorizationData,
) -> ContentYDocItemSchema:
    # TODO token expiration on access mode change
    match classroom_material.student_access_mode:
        case MaterialAccessMode.NO_ACCESS:
            raise MyMaterialResponses.MATERIAL_ACCESS_DENIED
        case MaterialAccessMode.READ_ONLY:
            can_upload_files = False
            ydoc_access_level = YDocAccessLevel.READ_ONLY
        case MaterialAccessMode.READ_WRITE:
            can_upload_files = True
            ydoc_access_level = YDocAccessLevel.READ_WRITE
        case _:
            assert_never(classroom_material.student_access_mode)

    return materials_svc.build_ydoc_item(
        material=classroom_material,
        user_id=auth_data.user_id,
        can_upload_files=can_upload_files,
        can_add_library_files=False,
        ydoc_access_level=ydoc_access_level,
    )
