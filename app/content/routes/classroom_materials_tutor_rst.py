from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Path, Query
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.content_sch import ContentYDocItemSchema, YDocAccessLevel
from app.content.dependencies.classroom_materials_dep import MyClassroomMaterialByIDs
from app.content.dependencies.materials_dep import (
    MaterialResponses,
    MyMaterialResponses,
)
from app.content.models.materials_db import (
    ClassroomMaterial,
    ClassroomMaterialSearchRequestSchema,
    Material,
    MaterialTag,
)
from app.content.models.ydoc_files_db import YDocFile
from app.content.models.ydocs_db import YDoc
from app.content.services import materials_svc

router = APIRouterExt(tags=["tutor classroom materials"])


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/materials/searches/",
    response_model=list[ClassroomMaterial.ResponseSchema],
    summary="List paginated materials in a classroom by id",
)
async def list_classroom_materials(
    classroom_id: Annotated[int, Path()],
    data: ClassroomMaterialSearchRequestSchema,
) -> Sequence[ClassroomMaterial]:
    return await ClassroomMaterial.find_paginated_by_classroom_id(
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
    auth_data: AuthorizationData,
    classroom_id: Annotated[int, Path()],
    input_data: ClassroomMaterial.InputSchema,
) -> ClassroomMaterial:
    main_ydoc = await YDoc.create(
        owner_id=auth_data.user_id,
        content_kind=input_data.content_kind,
    )
    return await ClassroomMaterial.create(
        main_ydoc=main_ydoc,
        **input_data.model_dump(exclude={"content_kind"}),
        classroom_id=classroom_id,
        material_tags=[],
    )


class DuplicateMaterialInputSchema(ClassroomMaterial.DuplicateInputSchema):
    source_id: UUID


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/material-duplicates/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomMaterial.ResponseSchema,
    responses=Responses.chain(MaterialResponses, MyMaterialResponses),
    summary="Duplicate any material to a classroom by id",
)
async def duplicate_material_to_classroom(
    auth_data: AuthorizationData,
    classroom_id: Annotated[int, Path()],
    input_data: DuplicateMaterialInputSchema,
    should_copy_tags: Annotated[bool, Query()] = True,
) -> ClassroomMaterial:
    source_material = await Material.find_first_by_id(input_data.source_id)
    if source_material is None:
        raise MaterialResponses.MATERIAL_NOT_FOUND
    if source_material.main_ydoc.owner_id != auth_data.user_id:
        raise MyMaterialResponses.MATERIAL_ACCESS_DENIED

    main_ydoc = await YDoc.duplicate_by_id(
        source_ydoc_id=source_material.main_ydoc_id,
        owner_id=auth_data.user_id,
    )
    await YDocFile.duplicate_all_links_by_ydoc_id(
        source_ydoc_id=source_material.main_ydoc_id,
        target_ydoc_id=main_ydoc.id,
    )
    return await ClassroomMaterial.create(
        main_ydoc=main_ydoc,
        **input_data.model_dump(exclude={"source_id"}),
        classroom_id=classroom_id,
        material_tags=(
            [
                MaterialTag(tag_id=material_tag.tag_id)
                for material_tag in source_material.material_tags
            ]
            if should_copy_tags
            else []
        ),
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
    summary="Retrieve a storage item for a classroom material by ids",
)
async def retrieve_classroom_material_storage_item(
    classroom_material: MyClassroomMaterialByIDs,
    auth_data: AuthorizationData,
) -> ContentYDocItemSchema:
    return materials_svc.build_ydoc_item(
        material=classroom_material,
        user_id=auth_data.user_id,
        can_upload_files=True,
        can_add_library_files=True,
        ydoc_access_level=YDocAccessLevel.READ_WRITE,
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
    classroom_material.update(**patch_data.model_dump(exclude_defaults=True))
    return classroom_material


@router.delete(
    path="/roles/tutor/classrooms/{classroom_id}/materials/{material_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a classroom material by ids",
)
async def delete_classroom_material(
    classroom_material: MyClassroomMaterialByIDs,
) -> None:
    await classroom_material.delete()
    await classroom_material.main_ydoc.delete()
