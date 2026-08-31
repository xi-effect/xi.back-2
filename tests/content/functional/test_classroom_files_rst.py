import random
from io import BytesIO
from typing import Literal
from uuid import UUID

import pytest
from faker import Faker
from freezegun import freeze_time
from PIL import Image
from pydantic import BaseModel
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.content.models.files_db import ClassroomFile, File
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.utils import repackage_json
from tests.content.conftest import CONTENT_TYPES_AND_FILE_EXTENSIONS, FileInputData

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_uploading_file_to_classroom(
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
    parametrized_file_input_data: FileInputData,
    classroom_id: int,
) -> None:
    file_id: UUID = assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/files/",
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

        assert (
            await ClassroomFile.find_first_by_ids(
                file_id=file.id,
                classroom_id=classroom_id,
            )
            is not None
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
async def test_uploading_file_to_classroom_content_type_mismatch(
    faker: Faker,
    tutor_client: TestClient,
    classroom_id: int,
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
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/files/",
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


async def test_adding_library_file_to_classroom(
    active_session: ActiveSession,
    tutor_client: TestClient,
    file: File,
    classroom_id: int,
) -> None:
    assert_nodata_response(
        tutor_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/files/{file.id}/"
        )
    )

    async with active_session():
        assert (
            await ClassroomFile.find_first_by_ids(
                file_id=file.id,
                classroom_id=classroom_id,
            )
            is not None
        )


async def test_adding_library_file_to_classroom_classroom_file_already_exists(
    active_session: ActiveSession,
    tutor_client: TestClient,
    file: File,
    classroom_id: int,
    classroom_file: ClassroomFile,
) -> None:
    assert_nodata_response(
        tutor_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/files/{file.id}/"
        )
    )

    async with active_session():
        assert (
            await ClassroomFile.find_first_by_ids(
                file_id=file.id,
                classroom_id=classroom_id,
            )
            is not None
        )


async def test_adding_library_file_to_classroom_file_access_denied(
    outsider_client: TestClient,
    file: File,
    classroom_id: int,
) -> None:
    assert_response(
        outsider_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/files/{file.id}/"
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "File access denied"},
    )


async def test_adding_library_file_to_classroom_file_not_found(
    tutor_client: TestClient,
    missing_file_id: UUID,
    classroom_id: int,
) -> None:
    assert_response(
        tutor_client.put(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/files/{missing_file_id}/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "File not found"},
    )


classroom_file_role_parametrization = pytest.mark.parametrize(
    "role",
    [
        pytest.param("student", id="student"),
        pytest.param("tutor", id="tutor"),
    ],
)

classroom_file_role_response_parametrization = pytest.mark.parametrize(
    ("role", "response_schema"),
    [
        pytest.param("student", File.StudentResponseSchema, id="student"),
        pytest.param("tutor", File.TutorResponseSchema, id="tutor"),
    ],
)


@classroom_file_role_response_parametrization
async def test_classroom_file_meta_retrieving(
    authorized_client: TestClient,
    file: File,
    classroom_id: int,
    classroom_file: ClassroomFile,
    role: Literal["student", "tutor"],
    response_schema: type[BaseModel],
) -> None:
    assert_response(
        authorized_client.get(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/{file.id}/meta/"
        ),
        expected_json=repackage_json(response_schema, file),
    )


@classroom_file_role_parametrization
async def test_classroom_file_retrieving(
    authorized_client: TestClient,
    parametrized_file_input_data: FileInputData,
    file: File,
    file_etag: str,
    file_last_modified: str,
    classroom_id: int,
    classroom_file: ClassroomFile,
    role: Literal["student", "tutor"],
) -> None:
    response = assert_response(
        authorized_client.get(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/{file.id}/"
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


@classroom_file_role_parametrization
async def test_classroom_file_retrieving_not_modified_by_etag(
    authorized_client: TestClient,
    file: File,
    file_etag: str,
    classroom_id: int,
    classroom_file: ClassroomFile,
    role: Literal["student", "tutor"],
) -> None:
    assert_nodata_response(
        authorized_client.get(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/{file.id}/",
            headers={"If-None-Match": file_etag},
        ),
        expected_code=status.HTTP_304_NOT_MODIFIED,
        expected_headers={"ETag": file_etag},
    )


@classroom_file_role_parametrization
async def test_classroom_file_retrieving_not_modified_by_datetime(
    authorized_client: TestClient,
    file: File,
    file_etag: str,
    file_last_modified: str,
    classroom_id: int,
    classroom_file: ClassroomFile,
    role: Literal["student", "tutor"],
) -> None:
    assert_nodata_response(
        authorized_client.get(
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/{file.id}/",
            headers={"If-Modified-Since": file_last_modified},
        ),
        expected_code=status.HTTP_304_NOT_MODIFIED,
        expected_headers={"ETag": file_etag},
    )


async def test_removing_file_from_classroom(
    active_session: ActiveSession,
    tutor_client: TestClient,
    file: File,
    classroom_id: int,
    classroom_file: ClassroomFile,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/files/{file.id}/"
        )
    )

    async with active_session():
        assert (
            await ClassroomFile.find_first_by_ids(
                file_id=file.id,
                classroom_id=classroom_id,
            )
            is None
        )


classroom_file_request_parametrization = pytest.mark.parametrize(
    ("role", "method", "postfix"),
    [
        pytest.param("student", "GET", "/", id="student_retrieving"),
        pytest.param("student", "GET", "/meta/", id="student_retrieving_meta"),
        pytest.param("tutor", "GET", "/", id="tutor_retrieving"),
        pytest.param("tutor", "GET", "/meta/", id="tutor_retrieving_meta"),
        pytest.param("tutor", "DELETE", "/", id="tutor_removing"),
    ],
)


@classroom_file_request_parametrization
async def test_classroom_file_not_finding(
    authorized_client: TestClient,
    file: File,
    classroom_id: int,
    role: Literal["student", "tutor"],
    method: str,
    postfix: str,
) -> None:
    assert_response(
        authorized_client.request(
            method,
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/{file.id}{postfix}",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom file not found"},
    )


@classroom_file_request_parametrization
async def test_file_not_finding(
    authorized_client: TestClient,
    missing_file_id: UUID,
    classroom_id: int,
    role: Literal["student", "tutor"],
    method: str,
    postfix: str,
) -> None:
    assert_response(
        authorized_client.request(
            method,
            f"/api/protected/content-service/roles/{role}"
            f"/classrooms/{classroom_id}/files/{missing_file_id}{postfix}",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "File not found"},
    )
