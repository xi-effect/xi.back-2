from collections.abc import AsyncIterator, Sequence
from uuid import uuid4

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.materials.models.materials_db import MaterialContentKind, TutorMaterial
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.materials import factories

pytestmark = pytest.mark.anyio

MATERIALS_LIST_SIZE_PER_KIND = 3
MATERIAL_KINDS = list(MaterialContentKind)
MATERIALS_LIST_SIZE = MATERIALS_LIST_SIZE_PER_KIND * len(MATERIAL_KINDS)


@pytest.fixture()
async def tutor_materials(
    active_session: ActiveSession,
    faker: Faker,
    tutor_user_id: int,
) -> AsyncIterator[Sequence[TutorMaterial]]:
    tutor_materials: list[TutorMaterial] = []
    async with active_session():
        for i in range(MATERIALS_LIST_SIZE):
            tutor_materials.append(
                await TutorMaterial.create(
                    **factories.TutorMaterialInputFactory.build_python(
                        kind=MATERIAL_KINDS[i % len(MATERIAL_KINDS)],
                    ),
                    tutor_id=tutor_user_id,
                    access_group_id=uuid4(),
                    content_id=uuid4(),
                )
            )

    tutor_materials.sort(
        key=lambda tutor_material: tutor_material.created_at,
        reverse=True,
    )

    yield tutor_materials

    async with active_session():
        for tutor_material in tutor_materials:
            await tutor_material.delete()


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
async def test_tutor_materials_listing(
    tutor_client: TestClient,
    tutor_materials: Sequence[TutorMaterial],
    content_kind: MaterialContentKind,
    offset: int | None,
    limit: int,
) -> None:
    cursor = None if offset is None else tutor_materials[offset]

    assert_response(
        tutor_client.post(
            "/api/protected/material-service/roles/tutor/materials/searches/",
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
            TutorMaterial.ResponseSchema.model_validate(
                tutor_material, from_attributes=True
            ).model_dump(mode="json")
            for tutor_material in tutor_materials
            if tutor_material.content_kind == content_kind
            and (cursor is None or tutor_material.created_at < cursor.created_at)
        ][:limit],
    )


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(None, MATERIALS_LIST_SIZE, id="start_to_end"),
        pytest.param(None, MATERIALS_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(MATERIALS_LIST_SIZE // 2, MATERIALS_LIST_SIZE, id="middle_to_end"),
    ],
)
async def test_tutor_materials_listing_any_kind(
    tutor_client: TestClient,
    tutor_materials: Sequence[TutorMaterial],
    offset: int | None,
    limit: int,
) -> None:
    cursor = None if offset is None else tutor_materials[offset]

    assert_response(
        tutor_client.post(
            "/api/protected/material-service/roles/tutor/materials/searches/",
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
            TutorMaterial.ResponseSchema.model_validate(
                tutor_material, from_attributes=True
            ).model_dump(mode="json")
            for tutor_material in tutor_materials
            if cursor is None or tutor_material.created_at < cursor.created_at
        ][:limit],
    )
