from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from faker import Faker
from pydantic_marshals.contains import UnorderedLiteralCollection, assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.content.models.materials_db import Material, MaterialTag
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.id_provider import IDProvider
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import PytestRequest
from tests.factories import TagFactory

pytestmark = pytest.mark.anyio


@pytest.fixture()
def tag_ids(faker: Faker, id_provider: IDProvider) -> list[int]:
    return [
        id_provider.generate_id()
        for _ in range(faker.random_int(min=1, max=MaterialTag.max_count_per_material))
    ]


@pytest.fixture(
    params=[
        pytest.param(True, id="with_existing_tags"),
        pytest.param(False, id="no_existing_tags"),
    ],
)
async def existing_material_tags(
    faker: Faker,
    active_session: ActiveSession,
    id_provider: IDProvider,
    any_material: Material,
    request: PytestRequest[bool],
) -> AsyncIterator[None]:
    existing_material_tag_ids = (
        [
            id_provider.generate_id()
            for _ in range(
                faker.random_int(min=1, max=MaterialTag.max_count_per_material)
            )
        ]
        if request.param
        else []
    )

    async with active_session():
        for tag_id in existing_material_tag_ids:
            await MaterialTag.create(material_id=any_material.id, tag_id=tag_id)

    yield

    async with active_session():
        await MaterialTag.delete_by_kwargs(material_id=any_material.id)


@pytest.mark.usefixtures("existing_material_tags")
async def test_setting_material_tags(
    active_session: ActiveSession,
    autocomplete_respx_mock: MockRouter,
    tutor_user_id: int,
    tutor_client: TestClient,
    any_material: Material,
    tag_ids: list[int],
) -> None:
    autocomplete_bridge_mock = autocomplete_respx_mock.get(
        "/tag-kinds/generic/tags/",
    ).respond(
        json={str(tag_id): TagFactory.build_json(id=tag_id) for tag_id in tag_ids}
    )

    assert_nodata_response(
        tutor_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/materials/{any_material.id}/tags/",
            json={"tag_ids": tag_ids},
        )
    )

    async with active_session():
        material_tags = await MaterialTag.find_all_by_kwargs(
            material_id=any_material.id
        )
        assert_contains(
            [material_tag.tag_id for material_tag in material_tags],
            UnorderedLiteralCollection(tag_ids),
        )

    assert_last_httpx_request(
        autocomplete_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )
    last_request = autocomplete_bridge_mock.calls.last.request
    assert_contains(
        {
            "tag_ids": last_request.url.params.get_list("tag_ids"),
            "tutor_id": last_request.url.params.get("tutor_id"),
        },
        {
            "tag_ids": UnorderedLiteralCollection(str(tag_id) for tag_id in tag_ids),
            "tutor_id": str(tutor_user_id),
        },
    )


@pytest.mark.usefixtures("existing_material_tags")
async def test_setting_material_tags_to_empty_list(
    active_session: ActiveSession,
    autocomplete_respx_mock: MockRouter,
    tutor_client: TestClient,
    any_material: Material,
) -> None:
    assert_nodata_response(
        tutor_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/materials/{any_material.id}/tags/",
            json={"tag_ids": []},
        )
    )

    async with active_session():
        assert (
            await MaterialTag.find_first_by_kwargs(material_id=any_material.id) is None
        )

    autocomplete_respx_mock.calls.assert_not_called()


async def test_setting_material_tags_tag_not_found(
    autocomplete_respx_mock: MockRouter,
    tutor_user_id: int,
    tutor_client: TestClient,
    any_material: Material,
    tag_ids: list[int],
) -> None:
    autocomplete_bridge_mock = autocomplete_respx_mock.get(
        "/tag-kinds/generic/tags/",
    ).respond(json={})

    assert_response(
        tutor_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/materials/{any_material.id}/tags/",
            json={"tag_ids": tag_ids},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Tag not found"},
    )

    assert_last_httpx_request(
        autocomplete_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )
    last_request = autocomplete_bridge_mock.calls.last.request
    assert_contains(
        {
            "tag_ids": last_request.url.params.get_list("tag_ids"),
            "tutor_id": last_request.url.params.get("tutor_id"),
        },
        {
            "tag_ids": UnorderedLiteralCollection(str(tag_id) for tag_id in tag_ids),
            "tutor_id": str(tutor_user_id),
        },
    )


async def test_setting_material_tags_material_not_found(
    tutor_client: TestClient,
    deleted_any_material_id: UUID,
    tag_ids: list[int],
) -> None:
    assert_response(
        tutor_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/materials/{deleted_any_material_id}/tags/",
            json={"tag_ids": tag_ids},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Material not found"},
    )


async def test_setting_material_tags_material_access_denied(
    outsider_client: TestClient,
    any_material: Material,
    tag_ids: list[int],
) -> None:
    assert_response(
        outsider_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/materials/{any_material.id}/tags/",
            json={"tag_ids": tag_ids},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )
