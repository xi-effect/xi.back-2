from collections.abc import Sequence

from starlette import status

from app.common.config import storage_token_provider
from app.common.config_bdg import storage_v2_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.storage_sch import (
    StorageItemSchema,
    StorageTokenPayloadSchema,
    StorageYDocItemSchema,
    YDocAccessLevel,
)
from app.common.utils.datetime import datetime_utc_now
from app.materials.dependencies.tutor_materials_dep import MyTutorMaterialByID
from app.materials.models.materials_db import (
    MaterialSearchRequestSchema,
    TutorMaterial,
)
from app.materials.services import materials_svc

router = APIRouterExt(tags=["tutor materials"])


@router.post(
    path="/roles/tutor/materials/searches/",
    response_model=list[TutorMaterial.ResponseSchema],
    summary="List paginated tutor materials for the current user",
)
async def list_tutor_materials(
    auth_data: AuthorizationData,
    data: MaterialSearchRequestSchema,
) -> Sequence[TutorMaterial]:
    return await TutorMaterial.find_paginated_by_tutor(
        tutor_id=auth_data.user_id,
        search_params=data,
    )


@router.post(
    path="/roles/tutor/materials/",
    status_code=status.HTTP_201_CREATED,
    response_model=TutorMaterial.ResponseSchema,
    summary="Create a new tutor material for the current user",
)
async def create_tutor_material(
    input_data: TutorMaterial.InputSchema,
    auth_data: AuthorizationData,
) -> TutorMaterial:
    access_group_data = await storage_v2_bridge.create_access_group()
    return await TutorMaterial.create(
        **input_data.model_dump(),
        access_group_id=access_group_data.id,
        content_id=access_group_data.main_ydoc_id,
        tutor_id=auth_data.user_id,
    )


@router.get(
    path="/roles/tutor/materials/{material_id}/",
    response_model=TutorMaterial.ResponseSchema,
    summary="Retrieve tutor material by id",
)
async def retrieve_tutor_material(tutor_material: MyTutorMaterialByID) -> TutorMaterial:
    return tutor_material


@router.get(
    path="/roles/tutor/materials/{material_id}/storage-item/",
    summary="Retrieve a storage item for a tutor material by id",
)
async def retrieve_tutor_material_storage_item(
    tutor_material: MyTutorMaterialByID,
    auth_data: AuthorizationData,
) -> StorageItemSchema:
    # TODO add StorageFileItem-s (based on content_kind)
    return StorageYDocItemSchema(
        access_group_id=tutor_material.access_group_id,
        ydoc_id=tutor_material.content_id,
        storage_token=storage_token_provider.serialize_and_sign(
            StorageTokenPayloadSchema(
                access_group_id=tutor_material.access_group_id,
                user_id=auth_data.user_id,
                can_upload_files=True,
                can_read_files=True,
                ydoc_access_level=YDocAccessLevel.READ_WRITE,
            )
        ),
    )


@router.patch(
    path="/roles/tutor/materials/{material_id}/",
    response_model=TutorMaterial.ResponseSchema,
    summary="Update tutor material by id",
)
async def patch_tutor_material(
    tutor_material: MyTutorMaterialByID,
    patch_data: TutorMaterial.PatchSchema,
) -> TutorMaterial:
    tutor_material.update(
        **patch_data.model_dump(exclude_defaults=True),
        updated_at=datetime_utc_now(),
    )
    return tutor_material


@router.delete(
    path="/roles/tutor/materials/{material_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tutor material by id",
)
async def delete_tutor_material(tutor_material: MyTutorMaterialByID) -> None:
    await materials_svc.delete_material(material=tutor_material)
