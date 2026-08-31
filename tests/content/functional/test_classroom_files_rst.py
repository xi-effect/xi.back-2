from typing import Literal
from uuid import UUID

import pytest
from pydantic import BaseModel
from starlette import status
from starlette.testclient import TestClient

from app.content.models.files_db import ClassroomFile, File
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.utils import repackage_json
from tests.content.conftest import FileInputData

pytestmark = pytest.mark.anyio


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
