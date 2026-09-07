from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Literal

import pytest
from faker import Faker
from pydantic import BaseModel
from pydantic_marshals.contains import UnorderedLiteralCollection
from pytest_lazy_fixtures import lf
from starlette.testclient import TestClient

from app.content.models.files_db import ClassroomFile, File, FileKind, FileTag
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.id_provider import IDProvider
from tests.common.types import AnyJSON
from tests.common.utils import repackage_json
from tests.content.conftest import generate_name

pytestmark = pytest.mark.anyio

FILE_KINDS = list(FileKind)
UPLOADER_COUNT = 2
TAG_COUNT = 2
CLASSROOM_FILES_LIST_SIZE = UPLOADER_COUNT * len(FILE_KINDS) * (TAG_COUNT + 1)


@pytest.fixture()
def tag_ids(id_provider: IDProvider) -> Sequence[int]:
    return [id_provider.generate_id() for _ in range(TAG_COUNT)]


@pytest.fixture()
async def classroom_files(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    student_user_id: int,
    classroom_id: int,
    common_name_prefix: str,
    even_name_suffix: str,
    odd_name_suffix: str,
    tag_ids: Sequence[int],
) -> AsyncIterator[Sequence[File]]:
    uploader_ids = (tutor_user_id, student_user_id)
    classroom_files: list[File] = []
    async with active_session():
        for i in range(CLASSROOM_FILES_LIST_SIZE):
            name = generate_name(
                faker=faker,
                prefix=common_name_prefix,
                suffix=even_name_suffix if i % 2 == 0 else odd_name_suffix,
            )
            file = await File.create(
                owner_id=tutor_user_id,
                uploader_id=uploader_ids[i // len(FILE_KINDS) % UPLOADER_COUNT],
                name=name,
                extension=faker.file_extension(),
                kind=FILE_KINDS[i % len(FILE_KINDS)],
                content_type=faker.mime_type(),
                size_bytes=faker.pyint(min_value=1, max_value=1000000),
                file_tags=[],
            )
            await ClassroomFile.create(
                file_id=file.id,
                classroom_id=classroom_id,
            )
            classroom_files.append(file)

    classroom_files.sort(key=lambda file: file.created_at, reverse=True)

    async with active_session() as session:
        for i, file in enumerate(classroom_files):
            session.add(file)
            file.file_tags = [
                FileTag(tag_id=tag_id) for tag_id in tag_ids[: i % (TAG_COUNT + 1)]
            ]

    yield classroom_files

    async with active_session():
        for file in classroom_files:
            await FileTag.delete_by_kwargs(file_id=file.id)
            await File.delete_by_kwargs(id=file.id)


def convert_classroom_files(
    files: Sequence[File],
    response_schema: type[BaseModel],
) -> Iterator[AnyJSON]:
    yield from (
        {
            **repackage_json(response_schema, file),
            "tag_ids": UnorderedLiteralCollection(file.tag_ids),
        }
        for file in files
    )


classroom_file_list_role_parametrization = pytest.mark.parametrize(
    ("role", "response_schema"),
    [
        pytest.param("student", File.StudentResponseSchema, id="student"),
        pytest.param("tutor", File.TutorResponseSchema, id="tutor"),
    ],
)


@classroom_file_list_role_parametrization
@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(None, CLASSROOM_FILES_LIST_SIZE, id="start_to_end"),
        pytest.param(None, CLASSROOM_FILES_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            CLASSROOM_FILES_LIST_SIZE // 2,
            CLASSROOM_FILES_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_classroom_files_listing(
    authorized_client: TestClient,
    classroom_id: int,
    classroom_files: Sequence[File],
    role: Literal["student", "tutor"],
    response_schema: type[BaseModel],
    offset: int | None,
    limit: int,
) -> None:
    cursor = None if offset is None else classroom_files[offset]

    assert_response(
        authorized_client.post(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/searches/",
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
            convert_classroom_files(
                [
                    file
                    for file in classroom_files
                    if cursor is None or file.created_at < cursor.created_at
                ][:limit],
                response_schema,
            )
        ),
    )


@classroom_file_list_role_parametrization
@pytest.mark.parametrize(
    "kinds",
    [
        *[pytest.param([kind], id=kind) for kind in FILE_KINDS],
        pytest.param(FILE_KINDS, id="all_kinds"),
    ],
)
async def test_classroom_files_listing_filtered_by_kinds(
    authorized_client: TestClient,
    classroom_id: int,
    classroom_files: Sequence[File],
    role: Literal["student", "tutor"],
    response_schema: type[BaseModel],
    kinds: list[FileKind],
) -> None:
    assert_response(
        authorized_client.post(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/searches/",
            json={
                "limit": CLASSROOM_FILES_LIST_SIZE,
                "filters": {"kinds": kinds},
            },
        ),
        expected_json=list(
            convert_classroom_files(
                [file for file in classroom_files if file.kind in kinds],
                response_schema,
            )
        ),
    )


@classroom_file_list_role_parametrization
@pytest.mark.parametrize(
    "is_uploaded_by_owner",
    [
        pytest.param(True, id="uploaded_by_owner"),
        pytest.param(False, id="uploaded_by_other"),
    ],
)
async def test_classroom_files_listing_filtered_by_is_uploaded_by_owner(
    authorized_client: TestClient,
    classroom_id: int,
    classroom_files: Sequence[File],
    role: Literal["student", "tutor"],
    response_schema: type[BaseModel],
    is_uploaded_by_owner: bool,
) -> None:
    assert_response(
        authorized_client.post(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/searches/",
            json={
                "limit": CLASSROOM_FILES_LIST_SIZE,
                "filters": {"is_uploaded_by_owner": is_uploaded_by_owner},
            },
        ),
        expected_json=list(
            convert_classroom_files(
                [
                    file
                    for file in classroom_files
                    if is_uploaded_by_owner == (file.uploader_id == file.owner_id)
                ],
                response_schema,
            )
        ),
    )


@classroom_file_list_role_parametrization
@pytest.mark.parametrize(
    "tag_indexes",
    [
        pytest.param([0], id="single_tag"),
        pytest.param([0, 1], id="multiple_tags"),
    ],
)
async def test_classroom_files_listing_filtered_by_tag_ids(
    authorized_client: TestClient,
    classroom_id: int,
    tag_ids: Sequence[int],
    classroom_files: Sequence[File],
    role: Literal["student", "tutor"],
    response_schema: type[BaseModel],
    tag_indexes: list[int],
) -> None:
    filter_tag_ids = {tag_ids[tag_index] for tag_index in tag_indexes}

    assert_response(
        authorized_client.post(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/searches/",
            json={
                "limit": CLASSROOM_FILES_LIST_SIZE,
                "filters": {"tag_ids": list(filter_tag_ids)},
            },
        ),
        expected_json=list(
            convert_classroom_files(
                [
                    file
                    for file in classroom_files
                    if filter_tag_ids.issubset(file.tag_ids)
                ],
                response_schema,
            )
        ),
    )


@classroom_file_list_role_parametrization
@pytest.mark.parametrize(
    ("search", "swap_case"),
    [
        pytest.param(lf("common_name_prefix"), False, id="any-original_case"),
        pytest.param(lf("common_name_prefix"), True, id="any-swapped_case"),
        pytest.param(lf("even_name_suffix"), False, id="even_only"),
        pytest.param(lf("odd_name_suffix"), False, id="odd_only-original_case"),
        pytest.param(lf("odd_name_suffix"), True, id="odd_only-swapped_case"),
        pytest.param(lf("excluded_from_names"), False, id="no_results"),
    ],
)
async def test_classroom_files_listing_filtered_by_search(
    authorized_client: TestClient,
    classroom_id: int,
    classroom_files: Sequence[File],
    role: Literal["student", "tutor"],
    response_schema: type[BaseModel],
    search: str,
    swap_case: bool,
) -> None:
    assert_response(
        authorized_client.post(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/searches/",
            json={
                "limit": CLASSROOM_FILES_LIST_SIZE,
                "filters": {"search": search.swapcase() if swap_case else search},
            },
        ),
        expected_json=list(
            convert_classroom_files(
                [
                    file
                    for file in classroom_files
                    if search.lower() in file.name.lower()
                ],
                response_schema,
            )
        ),
    )
