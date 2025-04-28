from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from pydantic import AwareDatetime

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.utils.datetime import datetime_utc_now
from app.tutors.dependencies.materials_dep import MaterialByID
from app.tutors.models.materials_db import Material, MaterialKind

router = APIRouterExt(tags=["tutor materials"])


@router.get(
    path="/materials/",
    response_model=list[Material.ResponseSchema],
    summary="List paginated tutor materials for the current user",
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
    path="/materials/",
    status_code=201,
    response_model=Material.ResponseSchema,
    summary="Create a new tutor material for the current user",
)
async def create_material(
    auth_data: AuthorizationData, input_data: Material.InputSchema
) -> Material:
    return await Material.create(**input_data.model_dump(), tutor_id=auth_data.user_id)


@router.get(
    path="/materials/{material_id}/",
    response_model=Material.ResponseSchema,
    summary="Retrieve tutor material by id",
)
async def retrieve_material(material: MaterialByID) -> Material:
    material.update(last_opened_at=datetime_utc_now())
    return material


@router.patch(
    path="/materials/{material_id}/",
    response_model=Material.ResponseSchema,
    summary="Update tutor material by id",
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
    path="/materials/{material_id}/",
    status_code=204,
    summary="Delete tutor material by id",
)
async def delete_material(material: MaterialByID) -> None:
    await material.delete()
