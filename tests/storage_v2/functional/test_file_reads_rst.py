from uuid import UUID

import pytest
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import storage_token_provider
from app.common.schemas.storage_sch import StorageTokenPayloadSchema
from app.storage_v2.models.access_groups_db import AccessGroupFile
from app.storage_v2.models.files_db import (
    FILE_KIND_TO_CONTENT_DISPOSITION,
    ContentDisposition,
    File,
)
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.storage_v2 import factories
from tests.storage_v2.conftest import FileInputData

pytestmark = pytest.mark.anyio


@pytest.fixture()
def file_read_storage_token(
    authorized_user_id: int,
    access_group_file: AccessGroupFile,
) -> str:
    storage_token_payload: StorageTokenPayloadSchema = (
        factories.StorageTokenPayloadFactory.build(
            access_group_id=access_group_file.access_group_id,
            user_id=authorized_user_id,
            can_read_files=True,
        )
    )
    return storage_token_provider.serialize_and_sign(storage_token_payload)


async def test_file_meta_retrieving(
    authorized_client: TestClient,
    access_group_file: AccessGroupFile,
    file_data: AnyJSON,
    file_read_storage_token: str,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/storage-service/v2"
            f"/files/{access_group_file.file_id}/meta/",
            headers={"X-Storage-Token": file_read_storage_token},
        ),
        expected_json=file_data,
    )


async def test_file_reading(
    authorized_client: TestClient,
    parametrized_file_input_data: FileInputData,
    access_group_file: AccessGroupFile,
    file_read_storage_token: str,
    file_etag: str,
    file_last_modified: str,
) -> None:
    disposition_type: ContentDisposition = FILE_KIND_TO_CONTENT_DISPOSITION.get(
        parametrized_file_input_data.kind, "attachment"
    )

    response = assert_response(
        authorized_client.get(
            f"/api/protected/storage-service/v2/files/{access_group_file.file_id}/",
            headers={"X-Storage-Token": file_read_storage_token},
        ),
        expected_headers={
            "ETag": file_etag,
            "Last-Modified": file_last_modified,
            "Content-Type": str,
            "Content-Disposition": (
                f'{disposition_type}; filename="{parametrized_file_input_data.name}"'
            ),
        },
        expected_json=None,
    )
    assert response.content == parametrized_file_input_data.content


async def test_file_reading_not_modified_by_etag(
    authorized_client: TestClient,
    access_group_file: AccessGroupFile,
    file_read_storage_token: str,
    file_etag: str,
) -> None:
    assert_nodata_response(
        authorized_client.get(
            f"/api/protected/storage-service/v2/files/{access_group_file.file_id}/",
            headers={
                "X-Storage-Token": file_read_storage_token,
                "If-None-Match": file_etag,
            },
        ),
        expected_code=status.HTTP_304_NOT_MODIFIED,
        expected_headers={"ETag": file_etag},
    )


async def test_file_reading_not_modified_by_datetime(
    authorized_client: TestClient,
    access_group_file: AccessGroupFile,
    file_read_storage_token: str,
    file_etag: str,
    file_last_modified: str,
) -> None:
    assert_nodata_response(
        authorized_client.get(
            f"/api/protected/storage-service/v2/files/{access_group_file.file_id}/",
            headers={
                "X-Storage-Token": file_read_storage_token,
                "If-Modified-Since": file_last_modified,
            },
        ),
        expected_code=status.HTTP_304_NOT_MODIFIED,
        expected_headers={"ETag": file_etag},
    )


file_reading_request_parametrization = pytest.mark.parametrize(
    ("method", "postfix"),
    [
        pytest.param("GET", "/", id="reading"),
        pytest.param("GET", "/meta/", id="retrieving_meta"),
    ],
)


@pytest.mark.parametrize(
    "storage_token",
    [
        pytest.param(
            lfc(
                "storage_token_generator",
                lf("access_group_file.access_group_id"),
                lf("authorized_user_id"),
                can_read_files=False,
            ),
            id="insufficient_permissions",
        ),
        pytest.param(
            lfc(
                "storage_token_generator",
                lf("access_group.id"),
                lf("outsider_user_id"),
                can_read_files=True,
            ),
            id="incorrect_user",
        ),
        pytest.param(
            lfc(
                "storage_token_generator",
                lf("missing_access_group_id"),
                lf("authorized_user_id"),
                can_read_files=True,
            ),
            id="missing_access_group",
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
    file: File,
    storage_token: str,
    method: str,
    postfix: str,
) -> None:
    assert_response(
        authorized_client.request(
            method=method,
            url=f"/api/protected/storage-service/v2/files/{file.id}{postfix}",
            headers={"X-Storage-Token": storage_token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid storage token"},
    )


@file_reading_request_parametrization
async def test_file_not_finding(
    authorized_client: TestClient,
    missing_file_id: UUID,
    file_read_storage_token: str,
    method: str,
    postfix: str,
) -> None:
    assert_response(
        authorized_client.request(
            method,
            f"/api/protected/storage-service/v2/files/{missing_file_id}{postfix}",
            headers={"X-Storage-Token": file_read_storage_token},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "File not found"},
    )
