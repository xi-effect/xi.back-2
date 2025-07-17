from collections.abc import AsyncIterator, Sequence
from datetime import timezone
from uuid import uuid4

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.tutors.models.materials_db import Material, MaterialKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import remove_none_values
from tests.tutors.factories import MaterialInputFactory

pytestmark = pytest.mark.anyio


MATERIALS_LIST_SIZE_PER_KIND = 3
MATERIAL_KINDS = list(MaterialKind)
MATERIALS_LIST_SIZE = MATERIALS_LIST_SIZE_PER_KIND * len(MATERIAL_KINDS)


@pytest.fixture()
async def materials(
    active_session: ActiveSession,
    faker: Faker,
    tutor_user_id: int,
) -> AsyncIterator[Sequence[Material]]:
    materials: list[Material] = []
    async with active_session():
        for i in range(MATERIALS_LIST_SIZE):
            materials.append(
                await Material.create(
                    **MaterialInputFactory.build_python(
                        kind=MATERIAL_KINDS[i % len(MATERIAL_KINDS)],
                    ),
                    tutor_id=tutor_user_id,
                    ydoc_id=str(uuid4()),
                    last_opened_at=faker.date_time_this_month(
                        before_now=False,
                        after_now=True,
                        tzinfo=timezone.utc,
                    ),
                )
            )

    materials.sort(key=lambda material: material.last_opened_at, reverse=True)

    yield materials

    async with active_session():
        for material in materials:
            await material.delete()


@pytest.mark.parametrize(
    "kind",
    [pytest.param(member, id=member) for member in MaterialKind.__members__.values()],
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
async def test_materials_listing(
    tutor_client: TestClient,
    materials: Sequence[Material],
    kind: MaterialKind,
    offset: int | None,
    limit: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/tutor-service/materials/",
            params=remove_none_values(
                {
                    "limit": limit,
                    "last_opened_before": offset
                    and materials[
                        MATERIALS_LIST_SIZE - offset
                    ].last_opened_at.isoformat(),
                    "kind": kind,
                }
            ),
        ),
        expected_json=[
            Material.ResponseSchema.model_validate(obj=material, from_attributes=True)
            for material in materials
            if material.kind == kind
            and (
                offset is None
                or material.last_opened_at
                < materials[MATERIALS_LIST_SIZE - offset].last_opened_at
            )
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
async def test_materials_listing_any_kind(
    tutor_client: TestClient,
    materials: Sequence[Material],
    offset: int | None,
    limit: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/tutor-service/materials/",
            params=remove_none_values(
                {
                    "limit": limit,
                    "last_opened_before": offset
                    and materials[
                        MATERIALS_LIST_SIZE - offset
                    ].last_opened_at.isoformat(),
                }
            ),
        ),
        expected_json=[
            Material.ResponseSchema.model_validate(material, from_attributes=True)
            for material in materials
            if offset is None
            or material.last_opened_at
            < materials[MATERIALS_LIST_SIZE - offset].last_opened_at
        ][:limit],
    )
