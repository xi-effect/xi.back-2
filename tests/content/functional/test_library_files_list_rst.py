from collections.abc import AsyncIterator, Iterator, Sequence
from pathlib import Path

import pytest
from faker import Faker
from pydantic_marshals.contains import UnorderedLiteralCollection
from starlette.testclient import TestClient

from app.content.models.files_db import File, FileKind, FileTag
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.id_provider import IDProvider
from tests.common.types import AnyJSON
from tests.common.utils import repackage_json

pytestmark = pytest.mark.anyio

FILE_KINDS = list(FileKind)
UPLOADER_COUNT = 2
TAG_COUNT = 2
LIBRARY_FILES_LIST_SIZE = UPLOADER_COUNT * len(FILE_KINDS) * (TAG_COUNT + 1)


@pytest.fixture()
def tag_ids(id_provider: IDProvider) -> Sequence[int]:
    return [id_provider.generate_id() for _ in range(TAG_COUNT)]


@pytest.fixture()
async def library_files(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    student_user_id: int,
    tag_ids: Sequence[int],
) -> AsyncIterator[Sequence[File]]:
    uploader_ids = (tutor_user_id, student_user_id)
    library_files: list[File] = []
    async with active_session():
        for i in range(LIBRARY_FILES_LIST_SIZE):
            filename = Path(faker.file_name())
            library_files.append(
                await File.create(
                    owner_id=tutor_user_id,
                    uploader_id=uploader_ids[i // len(FILE_KINDS) % UPLOADER_COUNT],
                    name=filename.stem,
                    extension=filename.suffix.lstrip("."),
                    kind=FILE_KINDS[i % len(FILE_KINDS)],
                    content_type=faker.mime_type(),
                    size_bytes=faker.pyint(min_value=1, max_value=1000000),
                    file_tags=[],
                )
            )

    library_files.sort(key=lambda file: file.created_at, reverse=True)

    async with active_session() as session:
        for i, file in enumerate(library_files):
            session.add(file)
            file.file_tags = [
                FileTag(tag_id=tag_id) for tag_id in tag_ids[: i % (TAG_COUNT + 1)]
            ]

    yield library_files

    async with active_session():
        for file in library_files:
            await FileTag.delete_by_kwargs(file_id=file.id)
            await File.delete_by_kwargs(id=file.id)


def convert_library_files(files: Sequence[File]) -> Iterator[AnyJSON]:
    yield from (
        {
            **repackage_json(File.TutorResponseSchema, file),
            "tag_ids": UnorderedLiteralCollection(file.tag_ids),
        }
        for file in files
    )


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
        expected_json=list(
            convert_library_files(
                [
                    file
                    for file in library_files
                    if cursor is None or file.created_at < cursor.created_at
                ][:limit]
            )
        ),
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
        expected_json=list(
            convert_library_files(
                [file for file in library_files if file.kind in kinds]
            )
        ),
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
        expected_json=list(
            convert_library_files(
                [
                    file
                    for file in library_files
                    if is_uploaded_by_owner == (file.uploader_id == file.owner_id)
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
async def test_library_files_listing_filtered_by_tag_ids(
    tutor_client: TestClient,
    tag_ids: Sequence[int],
    library_files: Sequence[File],
    tag_indexes: list[int],
) -> None:
    filter_tag_ids = {tag_ids[tag_index] for tag_index in tag_indexes}

    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/files/searches/",
            json={
                "limit": LIBRARY_FILES_LIST_SIZE,
                "filters": {"tag_ids": list(filter_tag_ids)},
            },
        ),
        expected_json=list(
            convert_library_files(
                [
                    file
                    for file in library_files
                    if filter_tag_ids.issubset(file.tag_ids)
                ]
            )
        ),
    )
