from collections.abc import Sequence
from typing import Annotated

from fastapi import Path
from starlette import status

from app.common.config import storage_token_provider
from app.common.config_bdg import storage_v2_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.storage_sch import (
    StorageItemSchema,
    StorageTokenPayloadSchema,
    StorageYDocItemSchema,
    YDocAccessLevel,
)
from app.common.utils.datetime import datetime_utc_now
from app.materials.dependencies.classroom_materials_dep import MyClassroomMaterialByIDs
from app.materials.dependencies.materials_dep import (
    MaterialResponses,
    MyMaterialResponses,
)
from app.materials.models.materials_db import (
    ClassroomMaterial,
    MaterialSearchRequestSchema,
    TutorMaterial,
)
from app.materials.services import materials_svc

router = APIRouterExt(tags=["tutor classroom materials"])


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/materials/searches/",
    response_model=list[ClassroomMaterial.ResponseSchema],
    summary="List paginated materials in a classroom by id",
)
async def list_classroom_materials(
    classroom_id: int,
    data: MaterialSearchRequestSchema,
) -> Sequence[ClassroomMaterial]:
    return await ClassroomMaterial.find_paginated_by_classroom(
        classroom_id=classroom_id,
        only_accessible_to_students=False,
        search_params=data,
    )


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/materials/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomMaterial.ResponseSchema,
    summary="Create a new material in a classroom by id",
)
async def create_classroom_material(
    input_data: ClassroomMaterial.InputSchema,
    classroom_id: int,
) -> ClassroomMaterial:
    access_group_data = await storage_v2_bridge.create_access_group()
    return await ClassroomMaterial.create(
        **input_data.model_dump(),
        access_group_id=access_group_data.id,
        content_id=access_group_data.main_ydoc_id,
        classroom_id=classroom_id,
    )


class DuplicateMaterialInputSchema(ClassroomMaterial.DuplicateInputSchema):
    source_id: int


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/material-duplicates/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomMaterial.ResponseSchema,
    responses=Responses.chain(MaterialResponses, MyMaterialResponses),
    summary="Duplicate a tutor material to a classroom by id",
)
async def duplicate_tutor_material_to_classroom(
    input_data: DuplicateMaterialInputSchema,
    classroom_id: Annotated[int, Path()],
    auth_data: AuthorizationData,
) -> ClassroomMaterial:
    tutor_material = await TutorMaterial.find_first_by_id(input_data.source_id)
    if tutor_material is None:
        raise MaterialResponses.MATERIAL_NOT_FOUND
    if tutor_material.tutor_id != auth_data.user_id:
        raise MyMaterialResponses.MATERIAL_ACCESS_DENIED

    new_access_group_data = await storage_v2_bridge.duplicate_access_group(
        source_access_group_id=tutor_material.access_group_id
    )

    return await ClassroomMaterial.create(
        **input_data.model_dump(exclude={"source_id"}),
        access_group_id=new_access_group_data.id,
        content_id=new_access_group_data.main_ydoc_id,
        content_kind=tutor_material.content_kind,
        classroom_id=classroom_id,
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/materials/{material_id}/",
    response_model=ClassroomMaterial.ResponseSchema,
    summary="Retrieve a classroom material by ids",
)
async def retrieve_classroom_material(
    classroom_material: MyClassroomMaterialByIDs,
) -> ClassroomMaterial:
    return classroom_material


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/materials/{material_id}/storage-item/",
    summary="Retrieve a storage item for a tutor classroom material by ids",
)
async def retrieve_classroom_material_storage_item(
    classroom_material: MyClassroomMaterialByIDs,
    auth_data: AuthorizationData,
) -> StorageItemSchema:
    # TODO add StorageFileItem-s (based on content_kind)
    return StorageYDocItemSchema(
        access_group_id=classroom_material.access_group_id,
        ydoc_id=classroom_material.content_id,
        storage_token=storage_token_provider.serialize_and_sign(
            StorageTokenPayloadSchema(
                access_group_id=classroom_material.access_group_id,
                user_id=auth_data.user_id,
                can_upload_files=True,
                can_read_files=True,
                ydoc_access_level=YDocAccessLevel.READ_WRITE,
            )
        ),
    )


@router.patch(
    path="/roles/tutor/classrooms/{classroom_id}/materials/{material_id}/",
    response_model=ClassroomMaterial.ResponseSchema,
    summary="Update a classroom material by ids",
)
async def patch_classroom_material(
    classroom_material: MyClassroomMaterialByIDs,
    patch_data: ClassroomMaterial.PatchSchema,
) -> ClassroomMaterial:
    classroom_material.update(
        **patch_data.model_dump(exclude_defaults=True),
        updated_at=datetime_utc_now(),
    )
    return classroom_material


@router.delete(
    path="/roles/tutor/classrooms/{classroom_id}/materials/{material_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a classroom material by ids",
)
async def delete_classroom_material(
    classroom_material: MyClassroomMaterialByIDs,
) -> None:
    await materials_svc.delete_material(material=classroom_material)
