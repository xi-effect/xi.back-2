from collections.abc import AsyncIterator, Sequence
from typing import Literal
from uuid import uuid4

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.materials.models.materials_db import (
    ClassroomMaterial,
    MaterialAccessMode,
    MaterialContentKind,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.materials import factories

pytestmark = pytest.mark.anyio

MATERIAL_ACCESS_MODES = list(MaterialAccessMode)
MATERIALS_LIST_SIZE_PER_KIND = 3 * len(MATERIAL_ACCESS_MODES)
MATERIAL_KINDS = list(MaterialContentKind)
MATERIALS_LIST_SIZE = MATERIALS_LIST_SIZE_PER_KIND * len(MATERIAL_KINDS)


@pytest.fixture()
async def classroom_materials(
    active_session: ActiveSession,
    faker: Faker,
    classroom_id: int,
) -> AsyncIterator[Sequence[ClassroomMaterial]]:
    classroom_materials: list[ClassroomMaterial] = []
    async with active_session():
        for i in range(MATERIALS_LIST_SIZE):
            classroom_materials.append(
                await ClassroomMaterial.create(
                    **factories.ClassroomMaterialInputFactory.build_python(
                        kind=MATERIAL_KINDS[i % len(MATERIAL_KINDS)],
                        student_access_mode=MATERIAL_ACCESS_MODES[
                            i // len(MATERIAL_KINDS) % len(MATERIAL_ACCESS_MODES)
                        ],
                    ),
                    classroom_id=classroom_id,
                    access_group_id=uuid4(),
                    content_id=uuid4(),
                )
            )

    classroom_materials.sort(
        key=lambda classroom_material: classroom_material.created_at,
        reverse=True,
    )

    yield classroom_materials

    async with active_session():
        for classroom_material in classroom_materials:
            await classroom_material.delete()


classroom_material_list_role_parametrization = pytest.mark.parametrize(
    ("role", "is_tutor"),
    [
        pytest.param("student", False, id="student"),
        pytest.param("tutor", True, id="tutor"),
    ],
)


@classroom_material_list_role_parametrization
@pytest.mark.parametrize(
    "content_kind",
    [pytest.param(member, id=member) for member in MATERIAL_KINDS],
)
@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(None, MATERIALS_LIST_SIZE_PER_KIND, id="start_to_end"),
        pytest.param(None, MATERIALS_LIST_SIZE_PER_KIND // 2, id="start_to_middle"),
        pytest.param(
            MATERIALS_LIST_SIZE_PER_KIND // 2,
            MATERIALS_LIST_SIZE_PER_KIND,
            id="middle_to_end",
        ),
    ],
)
async def test_tutor_classroom_materials_listing(
    tutor_client: TestClient,
    classroom_id: int,
    classroom_materials: Sequence[ClassroomMaterial],
    role: Literal["student", "tutor"],
    is_tutor: bool,
    content_kind: MaterialContentKind,
    offset: int | None,
    limit: int,
) -> None:
    filtered_classroom_materials = [
        classroom_material
        for classroom_material in classroom_materials
        if is_tutor
        or classroom_material.student_access_mode
        in {MaterialAccessMode.READ_ONLY, MaterialAccessMode.READ_WRITE}
    ]

    cursor = None if offset is None else filtered_classroom_materials[offset]

    assert_response(
        tutor_client.post(
            f"/api/protected/material-service/roles/{role}"
            f"/classrooms/{classroom_id}/materials/searches/",
            json={
                "cursor": (
                    None
                    if cursor is None
                    else {"created_at": cursor.created_at.isoformat()}
                ),
                "limit": limit,
                "filters": {"content_type": content_kind},
            },
        ),
        expected_json=[
            ClassroomMaterial.ResponseSchema.model_validate(
                classroom_material, from_attributes=True
            ).model_dump(mode="json")
            for classroom_material in filtered_classroom_materials
            if classroom_material.content_kind == content_kind
            and (cursor is None or classroom_material.created_at < cursor.created_at)
        ][:limit],
    )


@classroom_material_list_role_parametrization
@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(None, MATERIALS_LIST_SIZE, id="start_to_end"),
        pytest.param(None, MATERIALS_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(MATERIALS_LIST_SIZE // 2, MATERIALS_LIST_SIZE, id="middle_to_end"),
    ],
)
async def test_tutor_classroom_materials_listing_any_kind(
    tutor_client: TestClient,
    classroom_id: int,
    classroom_materials: Sequence[ClassroomMaterial],
    role: Literal["student", "tutor"],
    is_tutor: bool,
    offset: int | None,
    limit: int,
) -> None:
    filtered_classroom_materials = [
        classroom_material
        for classroom_material in classroom_materials
        if is_tutor
        or classroom_material.student_access_mode
        in {MaterialAccessMode.READ_ONLY, MaterialAccessMode.READ_WRITE}
    ]

    cursor = None if offset is None else filtered_classroom_materials[offset]

    assert_response(
        tutor_client.post(
            f"/api/protected/material-service/roles/{role}"
            f"/classrooms/{classroom_id}/materials/searches/",
            json={
                "cursor": (
                    None
                    if cursor is None
                    else {"created_at": cursor.created_at.isoformat()}
                ),
                "limit": limit,
                "filters": {},
            },
        ),
        expected_json=[
            ClassroomMaterial.ResponseSchema.model_validate(
                classroom_material, from_attributes=True
            ).model_dump(mode="json")
            for classroom_material in filtered_classroom_materials
            if (cursor is None or classroom_material.created_at < cursor.created_at)
        ][:limit],
    )
