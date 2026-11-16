from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.content_sch import ContentYDocItemSchema, YDocAccessLevel
from app.content.dependencies.personal_materials_dep import MyPersonalMaterialByID
from app.content.models.materials_db import PersonalMaterial
from app.content.models.ydocs_db import YDoc
from app.content.services import materials_svc, storage_svc

router = APIRouterExt(tags=["personal materials"])


@router.post(
    path="/roles/tutor/personal-materials/",
    status_code=status.HTTP_201_CREATED,
    response_model=PersonalMaterial.ResponseSchema,
    responses=storage_svc.StorageLimitResponses.responses(),
    summary="Create a new personal material for the current user",
)
async def create_personal_material(
    auth_data: AuthorizationData,
    input_data: PersonalMaterial.InputSchema,
) -> PersonalMaterial:
    await storage_svc.ensure_owner_is_under_storage_limit(owner_id=auth_data.user_id)
    main_ydoc = await YDoc.create(
        owner_id=auth_data.user_id,
        content_kind=input_data.content_kind,
    )
    return await PersonalMaterial.create(
        main_ydoc=main_ydoc,
        **input_data.model_dump(exclude={"content_kind"}),
        tutor_id=auth_data.user_id,
        material_tags=[],
    )


@router.get(
    path="/roles/tutor/personal-materials/{material_id}/",
    response_model=PersonalMaterial.ResponseSchema,
    summary="Retrieve a personal material by id",
)
async def retrieve_personal_material(
    personal_material: MyPersonalMaterialByID,
) -> PersonalMaterial:
    return personal_material


@router.get(
    path="/roles/tutor/personal-materials/{material_id}/storage-item/",
    summary="Retrieve a storage item for a personal material by id",
)
async def retrieve_personal_material_storage_item(
    personal_material: MyPersonalMaterialByID,
    auth_data: AuthorizationData,
) -> ContentYDocItemSchema:
    if await storage_svc.has_owner_reached_storage_limit(
        owner_id=personal_material.main_ydoc.owner_id
    ):
        can_upload_files = False
        can_add_library_files = False
        ydoc_access_level = YDocAccessLevel.READ_ONLY
    else:
        can_upload_files = True
        can_add_library_files = True
        ydoc_access_level = YDocAccessLevel.READ_WRITE

    return materials_svc.build_ydoc_item(
        material=personal_material,
        user_id=auth_data.user_id,
        can_upload_files=can_upload_files,
        can_add_library_files=can_add_library_files,
        ydoc_access_level=ydoc_access_level,
    )


@router.patch(
    path="/roles/tutor/personal-materials/{material_id}/",
    response_model=PersonalMaterial.ResponseSchema,
    summary="Update a personal material by id",
)
async def patch_personal_material(
    personal_material: MyPersonalMaterialByID,
    patch_data: PersonalMaterial.PatchSchema,
) -> PersonalMaterial:
    personal_material.update(**patch_data.model_dump(exclude_defaults=True))
    return personal_material


@router.delete(
    path="/roles/tutor/personal-materials/{material_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a personal material by id",
)
async def delete_personal_material(
    personal_material: MyPersonalMaterialByID,
) -> None:
    await personal_material.delete()
    await personal_material.main_ydoc.delete()
