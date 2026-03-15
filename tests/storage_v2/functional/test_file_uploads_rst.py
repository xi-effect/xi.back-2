import random
from io import BytesIO
from uuid import UUID

import pytest
from faker import Faker
from PIL import Image
from pydantic_marshals.contains import assert_contains
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
                    parametrized_file_input_data.input_content,
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
            real_file_content = f.read()

        if parametrized_file_input_data.content_type.startswith("image/"):
            image_result = Image.open(BytesIO(real_file_content))
            try:
                image_result.verify()
            except Exception as e:
                raise AssertionError("Invalid resulting image") from e

            assert_contains(
                {
                    "image_format": image_result.format,
                    "image_content": real_file_content,
                },
                {
                    "image_format": "WEBP",
                    "image_content": parametrized_file_input_data.processed_content,
                },
            )
        else:
            assert real_file_content == parametrized_file_input_data.processed_content

        await file.delete()


CONTENT_TYPES_AND_FILE_EXTENSIONS: list[tuple[str, str]] = [
    ("image/avif", "avif"),
    ("image/bmp", "bmp"),
    ("image/gif", "gif"),
    ("image/x-icon", "ico"),
    ("image/jpeg", "jpe"),
    ("image/jpeg", "jpeg"),
    ("image/jpeg", "jpg"),
    ("image/jpx", "jpx"),
    ("image/png", "png"),
    ("image/tiff", "tif"),
    ("image/tiff", "tiff"),
    ("image/webp", "webp"),
]


@pytest.mark.parametrize(
    "file_input_data",
    [
        pytest.param(lf("webp_image_file_input_data"), id="webp"),
        pytest.param(lf("png_image_file_input_data"), id="png"),
    ],
)
async def test_image_file_uploading_content_type_mismatch(
    faker: Faker,
    authorized_client: TestClient,
    file_upload_storage_token: str,
    file_input_data: FileInputData,
) -> None:
    content_type, file_extension = random.choice(
        [
            (content_type, file_extension)
            for content_type, file_extension in CONTENT_TYPES_AND_FILE_EXTENSIONS
            if content_type != file_input_data.content_type
        ]
    )

    assert_response(
        authorized_client.post(
            "/api/protected/storage-service/v2/file-kinds/image/files/",
            headers={"X-Storage-Token": file_upload_storage_token},
            files={
                "upload": (
                    faker.file_name(extension=file_extension),
                    file_input_data.input_content,
                    content_type,
                )
            },
        ),
        expected_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        expected_json={"detail": "File content doesn't match the content-type header"},
    )


async def test_image_file_uploading_wrong_content_format(
    faker: Faker,
    authorized_client: TestClient,
    uncategorized_file_content: bytes,
    file_upload_storage_token: str,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/storage-service/v2/file-kinds/image/files/",
            headers={"X-Storage-Token": file_upload_storage_token},
            files={
                "upload": (
                    faker.file_name(extension="webp"),
                    uncategorized_file_content,
                    "image/webp",
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
                    parametrized_file_input_data.input_content,
                    parametrized_file_input_data.content_type,
                )
            },
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid storage token"},
    )
