from uuid import UUID

import pytest
from faker import Faker
from starlette import status
from starlette.testclient import TestClient

from app.content.models.files_db import File
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.utils import repackage_json
from tests.content.conftest import FileInputData

pytestmark = pytest.mark.anyio


async def test_library_file_meta_retrieving(
    tutor_client: TestClient,
    file: File,
) -> None:
    assert_response(
        tutor_client.get(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/meta/"
        ),
        expected_json=repackage_json(File.LibraryResponseSchema, file),
    )


async def test_library_file_retrieving(
    tutor_client: TestClient,
    parametrized_file_input_data: FileInputData,
    file: File,
    file_etag: str,
    file_last_modified: str,
) -> None:
    content_disposition = parametrized_file_input_data.content_disposition

    response = assert_response(
        tutor_client.get(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/"
        ),
        expected_headers={
            "ETag": file_etag,
            "Last-Modified": file_last_modified,
            "Content-Type": parametrized_file_input_data.stored_content_type,
            "Content-Disposition": (
                f'{content_disposition}; filename="{parametrized_file_input_data.name}"'
            ),
        },
        expected_json=None,
    )
    assert response.content == parametrized_file_input_data.processed_content


async def test_library_file_retrieving_not_modified_by_etag(
    tutor_client: TestClient,
    file: File,
    file_etag: str,
) -> None:
    assert_nodata_response(
        tutor_client.get(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/",
            headers={"If-None-Match": file_etag},
        ),
        expected_code=status.HTTP_304_NOT_MODIFIED,
        expected_headers={"ETag": file_etag},
    )


async def test_library_file_retrieving_not_modified_by_datetime(
    tutor_client: TestClient,
    file: File,
    file_etag: str,
    file_last_modified: str,
) -> None:
    assert_nodata_response(
        tutor_client.get(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/",
            headers={"If-Modified-Since": file_last_modified},
        ),
        expected_code=status.HTTP_304_NOT_MODIFIED,
        expected_headers={"ETag": file_etag},
    )


async def test_library_file_retrieving_invalid_if_modified_since(
    faker: Faker,
    tutor_client: TestClient,
    file: File,
) -> None:
    invalid_date = faker.word()
    assert_response(
        tutor_client.get(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/",
            headers={"If-Modified-Since": invalid_date},
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["header", "if-modified-since"],
                    "msg": (
                        f"Value error, time data '{invalid_date}' does not match "  # noqa: WPS323
                        "format '%a, %d %b %Y %H:%M:%S GMT'"
                    ),
                },
            ],
        },
    )


async def test_library_file_deleting(
    active_session: ActiveSession,
    tutor_client: TestClient,
    file: File,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/"
        )
    )

    async with active_session():
        assert await File.find_first_by_id(file.id) is None

    assert not file.path.exists()


library_file_request_parametrization = pytest.mark.parametrize(
    ("method", "postfix"),
    [
        pytest.param("GET", "/", id="retrieving"),
        pytest.param("GET", "/meta/", id="retrieving_meta"),
        pytest.param("DELETE", "/", id="deleting"),
    ],
)


@library_file_request_parametrization
async def test_library_file_access_denied(
    outsider_client: TestClient,
    file: File,
    method: str,
    postfix: str,
) -> None:
    assert_response(
        outsider_client.request(
            method,
            f"/api/protected/content-service/roles/tutor/files/{file.id}{postfix}",
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "File access denied"},
    )


@library_file_request_parametrization
async def test_library_file_not_finding(
    tutor_client: TestClient,
    missing_file_id: UUID,
    method: str,
    postfix: str,
) -> None:
    assert_response(
        tutor_client.request(
            method,
            "/api/protected/content-service/roles/tutor"
            f"/files/{missing_file_id}{postfix}",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "File not found"},
    )
