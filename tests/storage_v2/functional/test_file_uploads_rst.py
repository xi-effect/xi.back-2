from uuid import UUID

import pytest
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import storage_token_provider
from app.common.schemas.storage_sch import StorageTokenPayloadSchema
from app.storage_v2.models.access_groups_db import AccessGroup, AccessGroupFile
from app.storage_v2.models.files_db import File
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.storage_v2 import factories
from tests.storage_v2.conftest import FileInputData

pytestmark = pytest.mark.anyio


@pytest.fixture()
def file_upload_storage_token(
    authorized_user_id: int,
    access_group: AccessGroup,
) -> str:
    storage_token_payload: StorageTokenPayloadSchema = (
        factories.StorageTokenPayloadFactory.build(
            access_group_id=access_group.id,
            user_id=authorized_user_id,
            can_upload_files=True,
        )
    )
    return storage_token_provider.serialize_and_sign(storage_token_payload)


async def test_file_uploading(
    active_session: ActiveSession,
    authorized_client: TestClient,
    access_group: AccessGroup,
    parametrized_file_input_data: FileInputData,
    file_upload_storage_token: str,
) -> None:
    file_id: UUID = assert_response(
        authorized_client.post(
            "/api/protected/storage-service/v2"
            f"/file-kinds/{parametrized_file_input_data.kind}/files/",
            headers={"X-Storage-Token": file_upload_storage_token},
            files={
                "upload": (
                    parametrized_file_input_data.name,
                    parametrized_file_input_data.content,
                    parametrized_file_input_data.content_type,
                )
            },
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            "id": UUID,
            "name": parametrized_file_input_data.name,
            "kind": parametrized_file_input_data.kind,
        },
    ).json()["id"]

    async with active_session():
        access_group_file = await AccessGroupFile.find_first_by_ids(
            access_group_id=access_group.id,
            file_id=file_id,
        )
        assert access_group_file is not None
        await access_group_file.delete()

        file = await File.find_first_by_id(file_id)
        assert file is not None

        assert file.path.is_file()
        with file.path.open("rb") as f:
            assert f.read() == parametrized_file_input_data.content

        await file.delete()


async def test_image_file_uploading_wrong_content_format(
    authorized_client: TestClient,
    uncategorized_file_content: bytes,
    image_file_input_data: FileInputData,
    file_upload_storage_token: str,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/storage-service/v2/file-kinds/image/files/",
            headers={"X-Storage-Token": file_upload_storage_token},
            files={
                "upload": (
                    image_file_input_data.name,
                    uncategorized_file_content,
                    image_file_input_data.content_type,
                )
            },
        ),
        expected_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        expected_json={"detail": "Invalid file format"},
    )


@pytest.mark.parametrize(
    "storage_token",
    [
        pytest.param(
            lfc(
                "storage_token_generator",
                lf("access_group.id"),
                lf("authorized_user_id"),
                can_upload_files=False,
            ),
            id="insufficient_permissions",
        ),
        pytest.param(
            lfc(
                "storage_token_generator",
                lf("access_group.id"),
                lf("outsider_user_id"),
                can_upload_files=True,
            ),
            id="incorrect_user",
        ),
        pytest.param(
            lfc(
                "storage_token_generator",
                lf("missing_access_group_id"),
                lf("authorized_user_id"),
                can_upload_files=True,
            ),
            id="missing_access_group",
        ),
        pytest.param(
            lfc("faker.password"),
            id="malformed_token",
        ),
    ],
)
async def test_file_uploading_invalid_token(
    authorized_client: TestClient,
    parametrized_file_input_data: FileInputData,
    storage_token: str,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/storage-service/v2"
            f"/file-kinds/{parametrized_file_input_data.kind}/files/",
            headers={"X-Storage-Token": storage_token},
            files={
                "upload": (
                    parametrized_file_input_data.name,
                    parametrized_file_input_data.content,
                    parametrized_file_input_data.content_type,
                )
            },
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid storage token"},
    )
