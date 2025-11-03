from collections.abc import Sequence
from typing import assert_never

from app.common.config import storage_token_provider
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.storage_sch import (
    StorageItemSchema,
    StorageTokenPayloadSchema,
    StorageYDocItemSchema,
    YDocAccessLevel,
)
from app.materials.dependencies.classroom_materials_dep import (
    MyClassroomMaterialByIDs,
    MyStudentClassroomMaterialByIDs,
)
from app.materials.dependencies.materials_dep import MyMaterialResponses
from app.materials.models.materials_db import (
    ClassroomMaterial,
    MaterialAccessMode,
    MaterialSearchRequestSchema,
)

router = APIRouterExt(tags=["student classroom materials"])


@router.post(
    path="/roles/student/classrooms/{classroom_id}/materials/searches/",
    response_model=list[ClassroomMaterial.ResponseSchema],
    summary="List paginated materials in a classroom by id",
)
async def list_classroom_materials(
    classroom_id: int,
    data: MaterialSearchRequestSchema,
) -> Sequence[ClassroomMaterial]:
    return await ClassroomMaterial.find_paginated_by_classroom(
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
async def retrieve_classroom_material_access_token(
    classroom_material: MyClassroomMaterialByIDs,
    auth_data: AuthorizationData,
) -> StorageItemSchema:
    # TODO add StorageFileItem-s (based on content_kind)
    # TODO token expiration on access mode change
    match classroom_material.student_access_mode:
        case MaterialAccessMode.NO_ACCESS:
            raise MyMaterialResponses.MATERIAL_ACCESS_DENIED
        case MaterialAccessMode.READ_ONLY:
            storage_token_payload = StorageTokenPayloadSchema(
                access_group_id=classroom_material.access_group_id,
                user_id=auth_data.user_id,
                can_upload_files=False,
                can_read_files=True,
                ydoc_access_level=YDocAccessLevel.READ_ONLY,
            )
        case MaterialAccessMode.READ_WRITE:
            storage_token_payload = StorageTokenPayloadSchema(
                access_group_id=classroom_material.access_group_id,
                user_id=auth_data.user_id,
                can_upload_files=True,
                can_read_files=True,
                ydoc_access_level=YDocAccessLevel.READ_WRITE,
            )
        case _:
            assert_never(classroom_material.student_access_mode)

    return StorageYDocItemSchema(
        access_group_id=classroom_material.access_group_id,
        ydoc_id=classroom_material.content_id,
        storage_token=storage_token_provider.serialize_and_sign(storage_token_payload),
    )
