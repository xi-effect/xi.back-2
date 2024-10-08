from uuid import UUID

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.storage.models.files_db import File
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response

pytestmark = pytest.mark.anyio


async def retrieve_and_validate_file(
    active_session: ActiveSession,
    file_id: UUID,
    expected_content: bytes,
) -> File:
    async with active_session():
        file = await File.find_first_by_id(file_id)
    assert file is not None
    assert file.path.is_file()
    with file.path.open("rb") as f:
        assert f.read() == expected_content
    return file


async def test_attachment_uploading(
    faker: Faker,
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    attachment: bytes,
) -> None:
    filename: str = faker.file_name()

    file_id = assert_response(
        authorized_client.post(
            "/api/protected/storage-service/files/attachments/",
            files={"attachment": (filename, attachment, "application/octet-stream")},
        ),
        expected_code=201,
        expected_json={
            "id": UUID,
            "name": filename,
            "kind": "attachment",
            "creator_user_id": proxy_auth_data.user_id,
        },
    ).json()["id"]

    file = await retrieve_and_validate_file(
        active_session=active_session,
        file_id=file_id,
        expected_content=attachment,
    )

    async with active_session():
        await file.delete()


async def test_image_uploading(
    faker: Faker,
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    image: bytes,
) -> None:
    filename: str = faker.file_name(extension="webp")

    file_id = assert_response(
        authorized_client.post(
            "/api/protected/storage-service/files/images/",
            files={"image": (filename, image, "image/webp")},
        ),
        expected_code=201,
        expected_json={
            "id": UUID,
            "name": filename,
            "kind": "image",
            "creator_user_id": proxy_auth_data.user_id,
        },
    ).json()["id"]

    file = await retrieve_and_validate_file(
        active_session=active_session,
        file_id=file_id,
        expected_content=image,
    )

    async with active_session():
        await file.delete()


@pytest.mark.parametrize(
    "content_type",
    [
        pytest.param("application/octet-stream", id="content_type_octet_stream"),
        pytest.param("image/webp", id="content_type_webp"),
    ],
)
@pytest.mark.parametrize(
    "extension",
    [
        pytest.param("txt", id="extension_txt"),
        pytest.param("webp", id="extension_webp"),
    ],
)
async def test_image_uploading_wrong_format(
    faker: Faker,
    authorized_client: TestClient,
    attachment: bytes,
    content_type: str,
    extension: str,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/storage-service/files/images/",
            files={
                "image": (
                    faker.file_name(extension=extension),
                    attachment,
                    content_type,
                )
            },
        ),
        expected_code=415,
        expected_json={"detail": "Invalid image format"},
    )


async def test_file_reading(
    authorized_client: TestClient,
    file_content: bytes,
    file_content_type: str,
    file: File,
    file_etag: str,
    file_last_modified: str,
) -> None:
    response = assert_response(
        authorized_client.get(f"/api/protected/storage-service/files/{file.id}/"),
        expected_headers={
            "ETag": file_etag,
            "Last-Modified": file_last_modified,
            "Content-Type": file_content_type,
        },
        expected_json=None,
    )
    assert response.content == file_content


async def test_file_reading_not_modified_by_etag(
    authorized_client: TestClient,
    file: File,
    file_etag: str,
) -> None:
    assert_nodata_response(
        authorized_client.get(
            f"/api/protected/storage-service/files/{file.id}/",
            headers={"If-None-Match": file_etag},
        ),
        expected_code=304,
        expected_headers={"ETag": file_etag},
    )


async def test_file_reading_not_modified_by_datetime(
    authorized_client: TestClient,
    file: File,
    file_etag: str,
    file_last_modified: str,
) -> None:
    assert_nodata_response(
        authorized_client.get(
            f"/api/protected/storage-service/files/{file.id}/",
            headers={"If-Modified-Since": file_last_modified},
        ),
        expected_code=304,
        expected_headers={"ETag": file_etag},
    )


async def test_file_meta_retrieving(authorized_client: TestClient, file: File) -> None:
    assert_response(
        authorized_client.get(f"/api/protected/storage-service/files/{file.id}/meta/"),
        expected_json={
            "id": str(file.id),
            "name": file.name,
            "kind": file.kind,
            "creator_user_id": file.creator_user_id,
        },
    )


async def test_file_deleting(authorized_client: TestClient, file: File) -> None:
    assert_nodata_response(
        authorized_client.delete(f"/api/protected/storage-service/files/{file.id}/")
    )


@pytest.mark.parametrize(
    ("method", "postfix"),
    [
        pytest.param("GET", "/", id="reading"),
        pytest.param("DELETE", "/", id="deleting"),
        pytest.param("GET", "/meta/", id="retrieving_meta"),
    ],
)
async def test_file_not_finding(
    authorized_client: TestClient, missing_file_id: UUID, method: str, postfix: str
) -> None:
    assert_response(
        authorized_client.request(
            method, f"/api/protected/storage-service/files/{missing_file_id}{postfix}"
        ),
        expected_code=404,
        expected_json={"detail": "File not found"},
    )
