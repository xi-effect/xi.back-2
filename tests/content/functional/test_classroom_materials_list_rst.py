from collections.abc import AsyncIterator, Sequence
from typing import Literal

import pytest
from starlette.testclient import TestClient

from app.content.models.materials_db import (
    ClassroomMaterial,
    MaterialAccessMode,
    MaterialTag,
)
from app.content.models.ydocs_db import YDoc, YDocContentKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.id_provider import IDProvider
from tests.content import factories

pytestmark = pytest.mark.anyio

MATERIAL_ACCESS_MODES = list(MaterialAccessMode)
TAG_COUNT = 2
MATERIALS_LIST_SIZE_PER_KIND = (TAG_COUNT + 1) * len(MATERIAL_ACCESS_MODES)
YDOC_CONTENT_KINDS = list(YDocContentKind)
MATERIALS_LIST_SIZE = MATERIALS_LIST_SIZE_PER_KIND * len(YDOC_CONTENT_KINDS)


@pytest.fixture()
def tag_ids(id_provider: IDProvider) -> Sequence[int]:
    return [id_provider.generate_id() for _ in range(TAG_COUNT)]


@pytest.fixture()
async def classroom_materials(
    active_session: ActiveSession,
    tutor_user_id: int,
    classroom_id: int,
    tag_ids: Sequence[int],
) -> AsyncIterator[Sequence[ClassroomMaterial]]:
    classroom_materials: list[ClassroomMaterial] = []
    async with active_session():
        for i in range(MATERIALS_LIST_SIZE):
            input_data = factories.ClassroomMaterialInputFactory.build_python(
                content_kind=YDOC_CONTENT_KINDS[i % len(YDOC_CONTENT_KINDS)],
                student_access_mode=MATERIAL_ACCESS_MODES[
                    i // len(YDOC_CONTENT_KINDS) % len(MATERIAL_ACCESS_MODES)
                ],
            )
            main_ydoc = await YDoc.create(
                owner_id=tutor_user_id,
                content_kind=input_data.pop("content_kind"),
            )
            classroom_materials.append(
                await ClassroomMaterial.create(
                    main_ydoc=main_ydoc,
                    classroom_id=classroom_id,
                    **input_data,
                )
            )

    classroom_materials.sort(
        key=lambda classroom_material: classroom_material.updated_at,
        reverse=True,
    )

    async with active_session():
        for i, classroom_material in enumerate(classroom_materials):
            for tag_id in tag_ids[: i % (TAG_COUNT + 1)]:
                await MaterialTag.create(
                    material_id=classroom_material.id,
                    tag_id=tag_id,
                )

    yield classroom_materials

    async with active_session():
        for classroom_material in classroom_materials:
            await MaterialTag.delete_by_kwargs(material_id=classroom_material.id)
            await ClassroomMaterial.delete_by_kwargs(id=classroom_material.id)
            await YDoc.delete_by_kwargs(id=classroom_material.main_ydoc_id)


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
    [
        pytest.param(content_kind, id=content_kind)
        for content_kind in YDOC_CONTENT_KINDS
    ],
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
async def test_classroom_materials_listing(
    authorized_client: TestClient,
    classroom_id: int,
    classroom_materials: Sequence[ClassroomMaterial],
    role: Literal["student", "tutor"],
    is_tutor: bool,
    content_kind: YDocContentKind,
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
        authorized_client.post(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/materials/searches/",
            json={
                "cursor": (
                    None
                    if cursor is None
                    else {"updated_at": cursor.updated_at.isoformat()}
                ),
                "limit": limit,
                "filters": {"content_kind": content_kind},
            },
        ),
        expected_json=[
            ClassroomMaterial.ResponseSchema.model_validate(
                classroom_material, from_attributes=True
            ).model_dump(mode="json")
            for classroom_material in filtered_classroom_materials
            if classroom_material.content_kind == content_kind
            and (cursor is None or classroom_material.updated_at < cursor.updated_at)
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
async def test_classroom_materials_listing_any_kind(
    authorized_client: TestClient,
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
        authorized_client.post(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/materials/searches/",
            json={
                "cursor": (
                    None
                    if cursor is None
                    else {"updated_at": cursor.updated_at.isoformat()}
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
            if (cursor is None or classroom_material.updated_at < cursor.updated_at)
        ][:limit],
    )


@classroom_material_list_role_parametrization
@pytest.mark.parametrize(
    "tag_indexes",
    [
        pytest.param([0], id="single_tag"),
        pytest.param([0, 1], id="multiple_tags"),
    ],
)
async def test_classroom_materials_listing_filtered_by_tag_ids(
    authorized_client: TestClient,
    classroom_id: int,
    tag_ids: Sequence[int],
    classroom_materials: Sequence[ClassroomMaterial],
    role: Literal["student", "tutor"],
    is_tutor: bool,
    tag_indexes: list[int],
) -> None:
    filter_tag_ids = {tag_ids[tag_index] for tag_index in tag_indexes}

    assert_response(
        authorized_client.post(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/materials/searches/",
            json={
                "limit": MATERIALS_LIST_SIZE,
                "filters": {"tag_ids": list(filter_tag_ids)},
            },
        ),
        expected_json=[
            ClassroomMaterial.ResponseSchema.model_validate(
                classroom_material, from_attributes=True
            ).model_dump(mode="json")
            for i, classroom_material in enumerate(classroom_materials)
            if (
                is_tutor
                or classroom_material.student_access_mode
                in {MaterialAccessMode.READ_ONLY, MaterialAccessMode.READ_WRITE}
            )
            and filter_tag_ids.issubset(tag_ids[: i % (TAG_COUNT + 1)])
        ],
    )
