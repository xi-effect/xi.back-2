import random
from io import BytesIO
from uuid import UUID

import pytest
from faker import Faker
from freezegun import freeze_time
from PIL import Image
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.content.models.files_db import ClassroomFile, File
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.id_provider import IDProvider
from tests.common.utils import repackage_json
from tests.content.conftest import CONTENT_TYPES_AND_FILE_EXTENSIONS, FileInputData

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_library_file_uploading(
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
    parametrized_file_input_data: FileInputData,
) -> None:
    file_id: UUID = assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/files/",
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
            "extension": parametrized_file_input_data.stored_extension,
            "kind": parametrized_file_input_data.kind,
            "uploader_id": tutor_user_id,
            "size_bytes": len(parametrized_file_input_data.processed_content),
            "created_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        file = await File.find_first_by_id(file_id)
        assert file is not None

        assert_contains(
            {"owner_id": file.owner_id, "content_type": file.content_type},
            {
                "owner_id": tutor_user_id,
                "content_type": parametrized_file_input_data.stored_content_type,
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


@pytest.mark.parametrize(
    "file_input_data",
    [
        pytest.param(lf("webp_image_file_input_data"), id="webp"),
        pytest.param(lf("png_image_file_input_data"), id="png"),
        pytest.param(lf("pdf_document_file_input_data"), id="pdf"),
        pytest.param(lf("wav_audio_file_input_data"), id="wav"),
        pytest.param(lf("pptx_presentation_file_input_data"), id="pptx"),
    ],
)
async def test_library_file_uploading_content_type_mismatch(
    faker: Faker,
    tutor_client: TestClient,
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
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/files/",
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


async def test_library_file_meta_retrieving(
    tutor_client: TestClient,
    file: File,
) -> None:
    assert_response(
        tutor_client.get(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/meta/"
        ),
        expected_json=repackage_json(File.TutorResponseSchema, file),
    )


async def test_library_file_retrieving(
    tutor_client: TestClient,
    parametrized_file_input_data: FileInputData,
    file: File,
    file_etag: str,
    file_last_modified: str,
) -> None:
    response = assert_response(
        tutor_client.get(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/"
        ),
        expected_headers={
            "ETag": file_etag,
            "Last-Modified": file_last_modified,
            "Content-Type": parametrized_file_input_data.stored_content_type,
            "Content-Disposition": (
                f"{parametrized_file_input_data.content_disposition};"
                f' filename="{parametrized_file_input_data.stored_name}"'
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


async def test_library_file_classroom_ids_listing(
    faker: Faker,
    active_session: ActiveSession,
    id_provider: IDProvider,
    tutor_client: TestClient,
    file: File,
) -> None:
    classroom_ids = [id_provider.generate_id() for _ in range(faker.random_int(2, 5))]
    async with active_session():
        for classroom_id in classroom_ids:
            await ClassroomFile.create(
                file_id=file.id,
                classroom_id=classroom_id,
            )

    assert_response(
        tutor_client.get(
            f"/api/protected/content-service/roles/tutor/files/{file.id}/classroom-ids/"
        ),
        expected_json=classroom_ids,
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
        pytest.param("GET", "/classroom-ids/", id="listing_classroom_ids"),
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
