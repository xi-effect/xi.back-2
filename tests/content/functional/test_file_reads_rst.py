from uuid import UUID

import pytest
from faker import Faker
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import content_token_provider
from app.common.schemas.content_sch import ContentTokenPayloadSchema
from app.content.models.files_db import (
    FILE_KIND_TO_CONTENT_DISPOSITION,
    ContentDisposition,
)
from app.content.models.ydoc_files_db import YDocFile
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.content import factories
from tests.content.conftest import ContentTokenGeneratorProtocol, FileInputData

pytestmark = pytest.mark.anyio


@pytest.fixture()
def file_read_content_token(
    authorized_user_id: int,
    material_id: UUID,
    ydoc_file: YDocFile,
) -> str:
    content_token_payload: ContentTokenPayloadSchema = (
        factories.ContentTokenPayloadFactory.build(
            material_id=material_id,
            ydoc_id=ydoc_file.ydoc_id,
            user_id=authorized_user_id,
            can_read_files=True,
        )
    )
    return content_token_provider.serialize_and_sign(content_token_payload)


async def test_file_meta_retrieving(
    authorized_client: TestClient,
    file_data: AnyJSON,
    ydoc_file: YDocFile,
    file_read_content_token: str,
) -> None:
    assert_response(
        authorized_client.get(
            f"/api/protected/content-service/files/{ydoc_file.file_id}/meta/",
            headers={"X-Content-Token": file_read_content_token},
        ),
        expected_json=file_data,
    )


async def test_file_reading(
    authorized_client: TestClient,
    parametrized_file_input_data: FileInputData,
    ydoc_file: YDocFile,
    file_etag: str,
    file_last_modified: str,
    file_read_content_token: str,
) -> None:
    disposition_type: ContentDisposition = FILE_KIND_TO_CONTENT_DISPOSITION.get(
        parametrized_file_input_data.kind, "attachment"
    )

    response = assert_response(
        authorized_client.get(
            f"/api/protected/content-service/files/{ydoc_file.file_id}/",
            headers={"X-Content-Token": file_read_content_token},
        ),
        expected_headers={
            "ETag": file_etag,
            "Last-Modified": file_last_modified,
            "Content-Type": parametrized_file_input_data.stored_content_type,
            "Content-Disposition": (
                f'{disposition_type}; filename="{parametrized_file_input_data.name}"'
            ),
        },
        expected_json=None,
    )
    assert response.content == parametrized_file_input_data.processed_content


async def test_file_reading_not_modified_by_etag(
    authorized_client: TestClient,
    ydoc_file: YDocFile,
    file_etag: str,
    file_read_content_token: str,
) -> None:
    assert_nodata_response(
        authorized_client.get(
            f"/api/protected/content-service/files/{ydoc_file.file_id}/",
            headers={
                "X-Content-Token": file_read_content_token,
                "If-None-Match": file_etag,
            },
        ),
        expected_code=status.HTTP_304_NOT_MODIFIED,
        expected_headers={"ETag": file_etag},
    )


async def test_file_reading_not_modified_by_datetime(
    authorized_client: TestClient,
    ydoc_file: YDocFile,
    file_etag: str,
    file_last_modified: str,
    file_read_content_token: str,
) -> None:
    assert_nodata_response(
        authorized_client.get(
            f"/api/protected/content-service/files/{ydoc_file.file_id}/",
            headers={
                "X-Content-Token": file_read_content_token,
                "If-Modified-Since": file_last_modified,
            },
        ),
        expected_code=status.HTTP_304_NOT_MODIFIED,
        expected_headers={"ETag": file_etag},
    )


async def test_file_reading_invalid_if_modified_since(
    faker: Faker,
    authorized_client: TestClient,
    ydoc_file: YDocFile,
    file_read_content_token: str,
) -> None:
    invalid_date = faker.word()
    assert_response(
        authorized_client.get(
            f"/api/protected/content-service/files/{ydoc_file.file_id}/",
            headers={
                "X-Content-Token": file_read_content_token,
                "If-Modified-Since": invalid_date,
            },
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


file_reading_request_parametrization = pytest.mark.parametrize(
    ("method", "postfix"),
    [
        pytest.param("GET", "/", id="reading"),
        pytest.param("GET", "/meta/", id="retrieving_meta"),
    ],
)


@pytest.mark.parametrize(
    "content_token",
    [
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("ydoc_file.ydoc_id"),
                lf("outsider_user_id"),
                can_read_files=True,
            ),
            id="incorrect_user",
        ),
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("other_ydoc.id"),
                lf("authorized_user_id"),
                can_read_files=True,
            ),
            id="wrong_ydoc",
        ),
        pytest.param(
            lfc("faker.password"),
            id="malformed_token",
        ),
    ],
)
@file_reading_request_parametrization
async def test_file_reading_invalid_token(
    authorized_client: TestClient,
    ydoc_file: YDocFile,
    content_token: str,
    method: str,
    postfix: str,
) -> None:
    assert_response(
        authorized_client.request(
            method=method,
            url=f"/api/protected/content-service/files/{ydoc_file.file_id}{postfix}",
            headers={"X-Content-Token": content_token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid content token"},
    )


@file_reading_request_parametrization
async def test_file_reading_insufficient_permissions(
    authorized_user_id: int,
    authorized_client: TestClient,
    content_token_generator: ContentTokenGeneratorProtocol,
    material_id: UUID,
    ydoc_file: YDocFile,
    method: str,
    postfix: str,
) -> None:
    content_token = content_token_generator(
        material_id,
        ydoc_file.ydoc_id,
        authorized_user_id,
        can_read_files=False,
    )

    assert_response(
        authorized_client.request(
            method=method,
            url=f"/api/protected/content-service/files/{ydoc_file.file_id}{postfix}",
            headers={"X-Content-Token": content_token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Insufficient content token permissions"},
    )


@file_reading_request_parametrization
async def test_file_not_finding(
    authorized_client: TestClient,
    missing_file_id: UUID,
    file_read_content_token: str,
    method: str,
    postfix: str,
) -> None:
    assert_response(
        authorized_client.request(
            method,
            f"/api/protected/content-service/files/{missing_file_id}{postfix}",
            headers={"X-Content-Token": file_read_content_token},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "File not found"},
    )
