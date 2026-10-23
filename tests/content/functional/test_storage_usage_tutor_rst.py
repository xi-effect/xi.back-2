import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.content.models.files_db import File, FileKind
from app.content.models.ydocs_db import YDoc, YDocContentKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


async def test_storage_usage_retrieving(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
) -> None:
    file_sizes = [
        faker.pyint(min_value=1, max_value=1000000)
        for _ in range(faker.random_int(2, 5))
    ]
    ydoc_sizes = [
        faker.pyint(min_value=1, max_value=1000000)
        for _ in range(faker.random_int(2, 5))
    ]

    async with active_session():
        for size_bytes in file_sizes:
            await File.create(
                owner_id=tutor_user_id,
                uploader_id=tutor_user_id,
                name=faker.word(),
                extension=faker.file_extension(),
                kind=FileKind.UNCATEGORIZED,
                content_type=faker.mime_type(),
                size_bytes=size_bytes,
                file_tags=[],
            )
        for size_bytes in ydoc_sizes:
            await YDoc.create(
                owner_id=tutor_user_id,
                content_kind=YDocContentKind.NOTE,
                size_bytes=size_bytes,
            )

    assert_response(
        tutor_client.get("/api/protected/content-service/roles/tutor/storage-usage/"),
        expected_json={"total_storage_bytes": sum(file_sizes) + sum(ydoc_sizes)},
    )

    async with active_session():
        await File.delete_by_kwargs(owner_id=tutor_user_id)
        await YDoc.delete_by_kwargs(owner_id=tutor_user_id)


async def test_storage_usage_retrieving_without_content(
    tutor_client: TestClient,
) -> None:
    assert_response(
        tutor_client.get("/api/protected/content-service/roles/tutor/storage-usage/"),
        expected_json={"total_storage_bytes": 0},
    )
