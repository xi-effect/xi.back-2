from pathlib import Path
from secrets import choice
from typing import Any

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.config import (
    ALLOWED_FILE_EXTENSIONS,
    FILE_STORAGE_PATH_MUB,
    MAX_FILE_SIZE,
)
from app.files.models.files_db import File
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.files.utils import clear_file_storage, create_file

pytestmark = pytest.mark.anyio


async def test_upload_files(
    mub_client: TestClient,
    active_session: ActiveSession,
    files_data: dict[str, list[Any]],
) -> None:
    assert_nodata_response(
        mub_client.post("/mub/file-service/files", files=files_data["files"]),
    )
    async with active_session():
        assert await File.find_all_by_kwargs() is not None
    clear_file_storage(mub=True)


async def test_upload_file_conflict(
    mub_client: TestClient,
    file_data: dict[str, Any],
) -> None:
    assert_response(
        mub_client.post(
            "/mub/file-service/files",
            files=[file_data["file"], file_data["file"]],
        ),
        expected_code=409,
        expected_json={"detail": "Filename already in use"},
    )

    clear_file_storage(mub=True)


async def test_upload_file_extension_not_allowed(
    mub_client: TestClient,
    faker: Faker,
) -> None:
    file_to_upload = (
        "files",
        (
            faker.file_name(extension="wrong"),
            faker.binary(length=1),
            "multipart/form-data",
        ),
    )

    assert_response(
        mub_client.post("/mub/file-service/files", files=[file_to_upload]),
        expected_code=415,
        expected_json={"detail": "File extension not supported"},
    )


async def test_upload_file_size_too_large(
    mub_client: TestClient,
    faker: Faker,
) -> None:
    file_to_upload = (
        "files",
        (
            faker.file_name(extension=choice(ALLOWED_FILE_EXTENSIONS)),
            faker.binary(length=MAX_FILE_SIZE + 1),
            "multipart/form-data",
        ),
    )

    assert_response(
        mub_client.post("/mub/file-service/files", files=[file_to_upload]),
        expected_code=413,
        expected_json={"detail": "File size is too large"},
    )


async def test_retrieve_file(
    mub_client: TestClient,
    faker: Faker,
    active_session: ActiveSession,
    file_data: dict[str, Any],
) -> None:
    file_bytes = faker.pystr().encode("utf-8")
    await create_file(active_session, file_data["filename"], file_bytes, mub=True)

    response = mub_client.get(
        f"/mub/file-service/files/{file_data['filename']}",
    )

    assert response.status_code == 200
    assert response.text == file_bytes.decode("utf-8")


async def test_retrieve_file_not_found(
    mub_client: TestClient,
    faker: Faker,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/file-service/files/{faker.file_name}",
        ),
        expected_code=404,
        expected_json={"detail": "File not found"},
    )


async def test_delete_file(
    mub_client: TestClient,
    active_session: ActiveSession,
    file_data: dict[str, Any],
) -> None:
    await create_file(active_session, file_data["filename"], mub=True)

    assert_nodata_response(
        mub_client.delete(
            f"/mub/file-service/files/{file_data['filename']}",
        )
    )

    async with active_session():
        assert not Path(FILE_STORAGE_PATH_MUB, file_data["filename"]).exists()
        assert await File.find_first_by_kwargs(filename=file_data["filename"]) is None

    clear_file_storage(mub=True)


async def test_delete_file_not_found(
    mub_client: TestClient,
    faker: Faker,
) -> None:
    assert_response(
        mub_client.delete(
            f"/mub/file-service/files/{faker.file_name}",
        ),
        expected_code=404,
        expected_json={"detail": "File not found"},
    )


async def test_update_file(
    mub_client: TestClient,
    faker: Faker,
    active_session: ActiveSession,
    file_data: dict[str, Any],
) -> None:
    file_bytes = faker.pystr().encode("utf-8")
    await create_file(active_session, file_data["filename"], file_bytes, mub=True)

    updated_filename: str = faker.file_name(extension=choice(ALLOWED_FILE_EXTENSIONS))
    updated_file_bytes: bytes = faker.binary(length=1)

    assert_nodata_response(
        mub_client.put(
            f"/mub/file-service/files/{file_data['filename']}",
            files={
                "single_file": (
                    updated_filename,
                    updated_file_bytes,
                    "multipart/form-data",
                )
            },
        ),
        expected_code=204,
    )

    async with active_session():
        assert await File.find_first_by_kwargs(filename=file_data["filename"]) is None
        assert await File.find_first_by_kwargs(filename=updated_filename) is not None

    assert Path(FILE_STORAGE_PATH_MUB, updated_filename).exists()
    assert not Path(FILE_STORAGE_PATH_MUB, file_data["filename"]).exists()

    with Path(FILE_STORAGE_PATH_MUB, updated_filename).open("rb") as f:
        assert f.read() == updated_file_bytes

    clear_file_storage(mub=True)


async def test_update_file_not_found(
    mub_client: TestClient,
    faker: Faker,
    file_data: dict[str, Any],
) -> None:
    assert_response(
        mub_client.put(
            f"/mub/file-service/files/{file_data['filename']}",
            files={
                "single_file": (
                    faker.file_name(extension=choice(ALLOWED_FILE_EXTENSIONS)),
                    faker.binary(length=1),
                    "multipart/form-data",
                )
            },
        ),
        expected_code=404,
        expected_json={"detail": "File not found"},
    )


async def test_update_file_size_too_large(
    mub_client: TestClient,
    faker: Faker,
    file_data: dict[str, Any],
) -> None:
    assert_response(
        mub_client.put(
            f"/mub/file-service/files/{file_data['filename']}",
            files={
                "single_file": (
                    faker.file_name(extension=choice(ALLOWED_FILE_EXTENSIONS)),
                    faker.binary(length=MAX_FILE_SIZE + 1),
                    "multipart/form-data",
                )
            },
        ),
        expected_code=413,
        expected_json={"detail": "File size is too large"},
    )


async def test_update_file_extension_not_allowed(
    mub_client: TestClient,
    faker: Faker,
    file_data: dict[str, Any],
) -> None:
    assert_response(
        mub_client.put(
            f"/mub/file-service/files/{file_data['filename']}",
            files={
                "single_file": (
                    faker.file_name(extension="wrong"),
                    faker.binary(length=1),
                    "multipart/form-data",
                )
            },
        ),
        expected_code=415,
        expected_json={"detail": "File extension not supported"},
    )
