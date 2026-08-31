from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from faker import Faker
from pydantic_marshals.contains import UnorderedLiteralCollection, assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.content.models.files_db import File, FileTag
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
        for _ in range(faker.random_int(min=1, max=FileTag.max_count_per_file))
    ]


@pytest.fixture(
    params=[
        pytest.param(True, id="with_existing_tags"),
        pytest.param(False, id="no_existing_tags"),
    ],
)
async def existing_file_tags(
    faker: Faker,
    active_session: ActiveSession,
    id_provider: IDProvider,
    file: File,
    request: PytestRequest[bool],
) -> AsyncIterator[None]:
    existing_file_tag_ids = (
        [
            id_provider.generate_id()
            for _ in range(faker.random_int(min=1, max=FileTag.max_count_per_file))
        ]
        if request.param
        else []
    )

    async with active_session():
        for tag_id in existing_file_tag_ids:
            await FileTag.create(file_id=file.id, tag_id=tag_id)

    yield

    async with active_session():
        await FileTag.delete_by_kwargs(file_id=file.id)


@pytest.mark.usefixtures("existing_file_tags")
async def test_setting_library_file_tags(
    active_session: ActiveSession,
    autocomplete_respx_mock: MockRouter,
    tutor_user_id: int,
    tutor_client: TestClient,
    file: File,
    tag_ids: list[int],
) -> None:
    autocomplete_bridge_mock = autocomplete_respx_mock.get(
        "/tag-kinds/generic/tags/",
    ).respond(
        json={str(tag_id): TagFactory.build_json(id=tag_id) for tag_id in tag_ids}
    )

    assert_nodata_response(
        tutor_client.put(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/tags/",
            json={"tag_ids": tag_ids},
        )
    )

    async with active_session():
        file_tags = await FileTag.find_all_by_kwargs(file_id=file.id)
        assert_contains(
            [file_tag.tag_id for file_tag in file_tags],
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


@pytest.mark.usefixtures("existing_file_tags")
async def test_setting_library_file_tags_to_empty_list(
    active_session: ActiveSession,
    autocomplete_respx_mock: MockRouter,
    tutor_client: TestClient,
    file: File,
) -> None:
    assert_nodata_response(
        tutor_client.put(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/tags/",
            json={"tag_ids": []},
        )
    )

    async with active_session():
        assert await FileTag.find_first_by_kwargs(file_id=file.id) is None

    autocomplete_respx_mock.calls.assert_not_called()


async def test_setting_library_file_tags_tag_not_found(
    autocomplete_respx_mock: MockRouter,
    tutor_user_id: int,
    tutor_client: TestClient,
    file: File,
    tag_ids: list[int],
) -> None:
    autocomplete_bridge_mock = autocomplete_respx_mock.get(
        "/tag-kinds/generic/tags/",
    ).respond(json={})

    assert_response(
        tutor_client.put(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/tags/",
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


async def test_setting_library_file_tags_file_not_found(
    tutor_client: TestClient,
    missing_file_id: UUID,
    tag_ids: list[int],
) -> None:
    assert_response(
        tutor_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/files/{missing_file_id}/tags/",
            json={"tag_ids": tag_ids},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "File not found"},
    )


async def test_setting_library_file_tags_file_access_denied(
    outsider_client: TestClient,
    file: File,
    tag_ids: list[int],
) -> None:
    assert_response(
        outsider_client.put(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/tags/",
            json={"tag_ids": tag_ids},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "File access denied"},
    )
