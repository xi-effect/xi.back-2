import random
from io import BytesIO
from uuid import UUID

import pytest
from faker import Faker
from freezegun import freeze_time
from PIL import Image
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import content_token_provider
from app.common.schemas.content_sch import ContentTokenPayloadSchema
from app.common.utils.datetime import datetime_utc_now
from app.content.models.files_db import File
from app.content.models.ydoc_files_db import YDocFile
from app.content.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.content import factories
from tests.content.conftest import FileInputData

pytestmark = pytest.mark.anyio


@pytest.fixture()
def file_upload_content_token(
    authorized_user_id: int,
    material_id: UUID,
    ydoc: YDoc,
) -> str:
    content_token_payload: ContentTokenPayloadSchema = (
        factories.ContentTokenPayloadFactory.build(
            material_id=material_id,
            ydoc_id=ydoc.id,
            user_id=authorized_user_id,
            can_upload_files=True,
        )
    )
    return content_token_provider.serialize_and_sign(content_token_payload)


@freeze_time()
async def test_file_uploading(
    active_session: ActiveSession,
    authorized_user_id: int,
    authorized_client: TestClient,
    material_id: UUID,
    ydoc: YDoc,
    parametrized_file_input_data: FileInputData,
) -> None:
    content_token = content_token_provider.serialize_and_sign(
        factories.ContentTokenPayloadFactory.build(
            material_id=material_id,
            ydoc_id=ydoc.id,
            user_id=authorized_user_id,
            can_upload_files=True,
        )
    )

    file_id: UUID = assert_response(
        authorized_client.post(
            "/api/protected/content-service"
            f"/file-kinds/{parametrized_file_input_data.kind}/files/",
            headers={"X-Content-Token": content_token},
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
            "name": parametrized_file_input_data.stem,
            "extension": parametrized_file_input_data.extension,
            "kind": parametrized_file_input_data.kind,
            "content_type": parametrized_file_input_data.stored_content_type,
            "size_bytes": len(parametrized_file_input_data.processed_content),
            "created_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        ydoc_file = await YDocFile.find_first_by_ids(
            ydoc_id=ydoc.id,
            file_id=file_id,
        )
        assert ydoc_file is not None

        file = await File.find_first_by_id(file_id)
        assert file is not None

        assert_contains(
            {
                "owner_id": file.owner_id,
                "uploader_id": file.uploader_id,
            },
            {
                "owner_id": ydoc.owner_id,
                "uploader_id": authorized_user_id,
            },
        )

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
    ("application/pdf", "pdf"),
    ("audio/aac", "aac"),
    ("audio/mpeg", "mp3"),
    ("audio/mp4", "m4a"),
    ("audio/ogg", "ogg"),
    ("audio/x-flac", "flac"),
    ("audio/x-wav", "wav"),
]


@pytest.mark.parametrize(
    "file_input_data",
    [
        pytest.param(lf("webp_image_file_input_data"), id="webp"),
        pytest.param(lf("png_image_file_input_data"), id="png"),
        pytest.param(lf("pdf_document_file_input_data"), id="pdf"),
        pytest.param(lf("wav_audio_file_input_data"), id="wav"),
    ],
)
async def test_file_uploading_content_type_mismatch(
    faker: Faker,
    authorized_client: TestClient,
    file_upload_content_token: str,
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
            f"/api/protected/content-service/file-kinds/{file_input_data.kind}/files/",
            headers={"X-Content-Token": file_upload_content_token},
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


@pytest.mark.parametrize(
    "file_input_data",
    [
        pytest.param(lf("webp_image_file_input_data"), id="image"),
        pytest.param(lf("pdf_document_file_input_data"), id="document"),
        pytest.param(lf("wav_audio_file_input_data"), id="audio"),
    ],
)
async def test_file_uploading_wrong_content_format(
    authorized_client: TestClient,
    uncategorized_file_content: bytes,
    file_upload_content_token: str,
    file_input_data: FileInputData,
) -> None:
    assert_response(
        authorized_client.post(
            f"/api/protected/content-service/file-kinds/{file_input_data.kind}/files/",
            headers={"X-Content-Token": file_upload_content_token},
            files={
                "upload": (
                    file_input_data.name,
                    uncategorized_file_content,
                    file_input_data.content_type,
                )
            },
        ),
        expected_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        expected_json={"detail": "Invalid file format"},
    )


@pytest.mark.parametrize(
    "content_token",
    [
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("ydoc.id"),
                lf("outsider_user_id"),
                can_upload_files=True,
            ),
            id="incorrect_user",
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
    content_token: str,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/content-service"
            f"/file-kinds/{parametrized_file_input_data.kind}/files/",
            headers={"X-Content-Token": content_token},
            files={
                "upload": (
                    parametrized_file_input_data.name,
                    parametrized_file_input_data.input_content,
                    parametrized_file_input_data.content_type,
                )
            },
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid content token"},
    )


@pytest.mark.parametrize(
    ("content_token", "expected_code", "expected_detail"),
    [
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("ydoc.id"),
                lf("authorized_user_id"),
                can_upload_files=False,
            ),
            status.HTTP_403_FORBIDDEN,
            "Insufficient content token permissions",
            id="insufficient_permissions",
        ),
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("missing_ydoc_id"),
                lf("authorized_user_id"),
                can_upload_files=True,
            ),
            status.HTTP_404_NOT_FOUND,
            "YDoc not found",
            id="missing_ydoc",
        ),
    ],
)
async def test_file_uploading_rejected(
    authorized_client: TestClient,
    parametrized_file_input_data: FileInputData,
    content_token: str,
    expected_code: int,
    expected_detail: str,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/content-service"
            f"/file-kinds/{parametrized_file_input_data.kind}/files/",
            headers={"X-Content-Token": content_token},
            files={
                "upload": (
                    parametrized_file_input_data.name,
                    parametrized_file_input_data.input_content,
                    parametrized_file_input_data.content_type,
                )
            },
        ),
        expected_code=expected_code,
        expected_json={"detail": expected_detail},
    )
