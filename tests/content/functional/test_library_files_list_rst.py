from collections.abc import AsyncIterator, Sequence
from pathlib import Path

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.content.models.files_db import File, FileKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import repackage_json

pytestmark = pytest.mark.anyio

FILE_KINDS = list(FileKind)
UPLOADER_COUNT = 2
LIBRARY_FILES_LIST_SIZE = UPLOADER_COUNT * len(FILE_KINDS)


@pytest.fixture()
async def library_files(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    student_user_id: int,
) -> AsyncIterator[Sequence[File]]:
    uploader_ids = (tutor_user_id, student_user_id)
    library_files: list[File] = []
    async with active_session():
        for i in range(LIBRARY_FILES_LIST_SIZE):
            filename = Path(faker.file_name())
            library_files.append(
                await File.create(
                    owner_id=tutor_user_id,
                    uploader_id=uploader_ids[i // len(FILE_KINDS)],
                    name=filename.stem,
                    extension=filename.suffix.lstrip("."),
                    kind=FILE_KINDS[i % len(FILE_KINDS)],
                    content_type=faker.mime_type(),
                    size_bytes=faker.pyint(min_value=1, max_value=1000000),
                )
            )

    library_files.sort(key=lambda file: file.created_at, reverse=True)

    yield library_files

    async with active_session():
        for file in library_files:
            await File.delete_by_kwargs(id=file.id)


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(None, LIBRARY_FILES_LIST_SIZE, id="start_to_end"),
        pytest.param(None, LIBRARY_FILES_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            LIBRARY_FILES_LIST_SIZE // 2,
            LIBRARY_FILES_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_library_files_listing(
    tutor_client: TestClient,
    library_files: Sequence[File],
    offset: int | None,
    limit: int,
) -> None:
    cursor = None if offset is None else library_files[offset]

    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/files/searches/",
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
            repackage_json(File.LibraryResponseSchema, file)
            for file in library_files
            if cursor is None or file.created_at < cursor.created_at
        ][:limit],
    )


@pytest.mark.parametrize(
    "kinds",
    [
        *[pytest.param([kind], id=kind) for kind in FILE_KINDS],
        pytest.param(FILE_KINDS, id="all_kinds"),
    ],
)
async def test_library_files_listing_filtered_by_kinds(
    tutor_client: TestClient,
    library_files: Sequence[File],
    kinds: list[FileKind],
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/files/searches/",
            json={
                "limit": LIBRARY_FILES_LIST_SIZE,
                "filters": {"kinds": kinds},
            },
        ),
        expected_json=[
            repackage_json(File.LibraryResponseSchema, file)
            for file in library_files
            if file.kind in kinds
        ],
    )


@pytest.mark.parametrize(
    "is_uploaded_by_owner",
    [
        pytest.param(True, id="uploaded_by_owner"),
        pytest.param(False, id="uploaded_by_other"),
    ],
)
async def test_library_files_listing_filtered_by_is_uploaded_by_owner(
    tutor_client: TestClient,
    library_files: Sequence[File],
    is_uploaded_by_owner: bool,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/files/searches/",
            json={
                "limit": LIBRARY_FILES_LIST_SIZE,
                "filters": {"is_uploaded_by_owner": is_uploaded_by_owner},
            },
        ),
        expected_json=[
            repackage_json(File.LibraryResponseSchema, file)
            for file in library_files
            if is_uploaded_by_owner == (file.uploader_id == file.owner_id)
        ],
    )
