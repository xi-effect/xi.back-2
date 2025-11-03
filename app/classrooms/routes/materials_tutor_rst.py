from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from pydantic import AwareDatetime
from starlette import status

from app.classrooms.dependencies.materials_dep import MaterialByID
from app.classrooms.models.materials_db import Material, MaterialKind
from app.classrooms.services import materials_svc
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.utils.datetime import datetime_utc_now

router = APIRouterExt(tags=["tutor materials"], deprecated=True)


@router.get(
    path="/roles/tutor/materials/",
    response_model=list[Material.ResponseSchema],
    summary="Use materials service instead",
)
async def list_materials(
    auth_data: AuthorizationData,
    limit: Annotated[int, Query(gt=0, le=50)] = 10,
    last_opened_before: AwareDatetime | None = None,
    kind: MaterialKind | None = None,
) -> Sequence[Material]:
    return await Material.find_paginated_by_tutor(
        tutor_id=auth_data.user_id,
        last_opened_before=last_opened_before,
        kind=kind,
        limit=limit,
    )


@router.post(
    path="/roles/tutor/materials/",
    status_code=status.HTTP_201_CREATED,
    response_model=Material.ResponseSchema,
    summary="Use materials service instead",
)
async def create_material(
    auth_data: AuthorizationData, input_data: Material.InputSchema
) -> Material:
    return await materials_svc.create_material(
        input_data=input_data, auth_data=auth_data
    )


@router.get(
    path="/roles/tutor/materials/{material_id}/",
    response_model=Material.ResponseSchema,
    summary="Use materials service instead",
)
async def retrieve_material(material: MaterialByID) -> Material:
    material.update(last_opened_at=datetime_utc_now())
    return material


@router.patch(
    path="/roles/tutor/materials/{material_id}/",
    response_model=Material.ResponseSchema,
    summary="Use materials service instead",
)
async def patch_material(
    material: MaterialByID,
    patch_data: Material.PatchSchema,
) -> Material:
    material.update(
        **patch_data.model_dump(exclude_defaults=True), updated_at=datetime_utc_now()
    )
    return material


@router.delete(
    path="/roles/tutor/materials/{material_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Use materials service instead",
)
async def delete_material(material: MaterialByID) -> None:
    await materials_svc.delete_material(material=material)
