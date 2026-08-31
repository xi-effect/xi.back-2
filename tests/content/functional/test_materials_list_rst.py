from collections.abc import AsyncIterator, Iterator, Sequence
from typing import assert_never

import pytest
from starlette.testclient import TestClient

from app.content.models.materials_db import (
    NAMED_MATERIAL_ACCESS_KINDS,
    AnyNamedMaterial,
    ClassroomMaterial,
    Material,
    MaterialAccessKind,
    MaterialTag,
    PersonalMaterial,
)
from app.content.models.ydocs_db import YDoc, YDocContentKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.id_provider import IDProvider
from tests.common.types import AnyJSON
from tests.content import factories

pytestmark = pytest.mark.anyio

YDOC_CONTENT_KINDS = list(YDocContentKind)
CLASSROOM_COUNT = 2
TAG_COUNT = 2
MATERIALS_LIST_SIZE_PER_KIND = (TAG_COUNT + 1) * (CLASSROOM_COUNT + 1)
MATERIALS_LIST_SIZE = MATERIALS_LIST_SIZE_PER_KIND * len(YDOC_CONTENT_KINDS)


@pytest.fixture()
def classroom_ids(id_provider: IDProvider) -> Sequence[int]:
    return [id_provider.generate_id() for _ in range(CLASSROOM_COUNT + 1)]


@pytest.fixture()
def tag_ids(id_provider: IDProvider) -> Sequence[int]:
    return [id_provider.generate_id() for _ in range(TAG_COUNT)]


@pytest.fixture()
async def materials(
    active_session: ActiveSession,
    tutor_user_id: int,
    classroom_ids: Sequence[int],
    tag_ids: Sequence[int],
) -> AsyncIterator[Sequence[AnyNamedMaterial]]:
    materials: list[AnyNamedMaterial] = []
    async with active_session():
        for i in range(MATERIALS_LIST_SIZE):
            content_kind = YDOC_CONTENT_KINDS[i % len(YDOC_CONTENT_KINDS)]
            classroom_index = i // len(YDOC_CONTENT_KINDS) % (CLASSROOM_COUNT + 1)
            if classroom_index == 0:
                input_data = factories.PersonalMaterialInputFactory.build_python(
                    content_kind=content_kind,
                )
                main_ydoc = await YDoc.create(
                    owner_id=tutor_user_id,
                    content_kind=input_data.pop("content_kind"),
                )
                materials.append(
                    await PersonalMaterial.create(
                        main_ydoc=main_ydoc,
                        tutor_id=tutor_user_id,
                        **input_data,
                    )
                )
            else:
                input_data = factories.ClassroomMaterialInputFactory.build_python(
                    content_kind=content_kind,
                )
                main_ydoc = await YDoc.create(
                    owner_id=tutor_user_id,
                    content_kind=input_data.pop("content_kind"),
                )
                materials.append(
                    await ClassroomMaterial.create(
                        main_ydoc=main_ydoc,
                        classroom_id=classroom_ids[classroom_index - 1],
                        **input_data,
                    )
                )

    materials.sort(key=lambda material: material.updated_at, reverse=True)

    async with active_session():
        for i, material in enumerate(materials):
            for tag_id in tag_ids[: i % (TAG_COUNT + 1)]:
                await MaterialTag.create(material_id=material.id, tag_id=tag_id)

    yield materials

    async with active_session():
        for material in materials:
            await MaterialTag.delete_by_kwargs(material_id=material.id)
            await Material.delete_by_kwargs(id=material.id)
            await YDoc.delete_by_kwargs(id=material.main_ydoc_id)


def convert_materials(materials: Sequence[AnyNamedMaterial]) -> Iterator[AnyJSON]:
    for material in materials:
        match material:
            case PersonalMaterial():
                yield PersonalMaterial.ResponseSchema.model_validate(
                    material, from_attributes=True
                ).model_dump(mode="json")
            case ClassroomMaterial():
                yield ClassroomMaterial.ResponseSchema.model_validate(
                    material, from_attributes=True
                ).model_dump(mode="json")
            case _:
                assert_never(material)


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
async def test_materials_listing(
    tutor_client: TestClient,
    materials: Sequence[AnyNamedMaterial],
    content_kind: YDocContentKind,
    offset: int | None,
    limit: int,
) -> None:
    cursor = None if offset is None else materials[offset]

    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/materials/searches/",
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
        expected_json=list(
            convert_materials(
                [
                    material
                    for material in materials
                    if material.content_kind == content_kind
                    and (cursor is None or material.updated_at < cursor.updated_at)
                ][:limit]
            )
        ),
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
    materials: Sequence[AnyNamedMaterial],
    offset: int | None,
    limit: int,
) -> None:
    cursor = None if offset is None else materials[offset]

    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/materials/searches/",
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
        expected_json=list(
            convert_materials(
                [
                    material
                    for material in materials
                    if cursor is None or material.updated_at < cursor.updated_at
                ][:limit]
            )
        ),
    )


@pytest.mark.parametrize(
    "access_kind",
    [
        pytest.param(access_kind, id=access_kind)
        for access_kind in NAMED_MATERIAL_ACCESS_KINDS
    ],
)
async def test_materials_listing_filtered_by_access_kind(
    tutor_client: TestClient,
    materials: Sequence[AnyNamedMaterial],
    access_kind: MaterialAccessKind,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/materials/searches/",
            json={
                "limit": MATERIALS_LIST_SIZE,
                "filters": {"scope": {"access_kind": access_kind}},
            },
        ),
        expected_json=list(
            convert_materials(
                [
                    material
                    for material in materials
                    if material.access_kind == access_kind
                ]
            )
        ),
    )


@pytest.mark.parametrize(
    "classroom_indexes",
    [
        pytest.param([0], id="single_classroom"),
        pytest.param([0, 1, 2], id="multiple_classrooms"),
        pytest.param([2], id="classroom_without_materials"),
    ],
)
async def test_materials_listing_filtered_by_classroom_ids(
    tutor_client: TestClient,
    classroom_ids: Sequence[int],
    materials: Sequence[AnyNamedMaterial],
    classroom_indexes: list[int],
) -> None:
    filter_classroom_ids = [
        classroom_ids[classroom_index] for classroom_index in classroom_indexes
    ]

    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/materials/searches/",
            json={
                "limit": MATERIALS_LIST_SIZE,
                "filters": {
                    "scope": {
                        "access_kind": MaterialAccessKind.CLASSROOM,
                        "classroom_ids": filter_classroom_ids,
                    },
                },
            },
        ),
        expected_json=list(
            convert_materials(
                [
                    material
                    for material in materials
                    if isinstance(material, ClassroomMaterial)
                    and material.classroom_id in filter_classroom_ids
                ]
            )
        ),
    )


@pytest.mark.parametrize(
    "tag_indexes",
    [
        pytest.param([0], id="single_tag"),
        pytest.param([0, 1], id="multiple_tags"),
    ],
)
async def test_materials_listing_filtered_by_tag_ids(
    tutor_client: TestClient,
    tag_ids: Sequence[int],
    materials: Sequence[AnyNamedMaterial],
    tag_indexes: list[int],
) -> None:
    filter_tag_ids = {tag_ids[tag_index] for tag_index in tag_indexes}

    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/materials/searches/",
            json={
                "limit": MATERIALS_LIST_SIZE,
                "filters": {"tag_ids": list(filter_tag_ids)},
            },
        ),
        expected_json=list(
            convert_materials(
                [
                    material
                    for i, material in enumerate(materials)
                    if filter_tag_ids.issubset(tag_ids[: i % (TAG_COUNT + 1)])
                ]
            )
        ),
    )
