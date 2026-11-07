import random
from uuid import UUID

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import UnorderedLiteralCollection
from pytest_lazy_fixtures import lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import content_token_provider
from app.common.schemas.content_sch import ContentTokenPayloadSchema, YDocAccessLevel
from app.content.models.materials_db import ClassroomMaterial, MaterialAccessMode
from app.content.services import storage_svc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_classroom_material_retrieving(
    active_session: ActiveSession,
    student_client: TestClient,
    classroom_material: ClassroomMaterial,
    classroom_material_data: AnyJSON,
    classroom_material_tag_ids: list[int],
) -> None:
    student_access_mode = random.choice(
        [MaterialAccessMode.READ_WRITE, MaterialAccessMode.READ_ONLY]
    )

    async with active_session() as session:
        session.add(classroom_material)
        classroom_material.student_access_mode = student_access_mode

    assert_response(
        student_client.get(
            "/api/protected/content-service/roles/student"
            f"/classrooms/{classroom_material.classroom_id}"
            f"/materials/{classroom_material.id}/"
        ),
        expected_json={
            **classroom_material_data,
            "student_access_mode": student_access_mode,
            "tag_ids": UnorderedLiteralCollection(classroom_material_tag_ids),
        },
    )


@freeze_time()
@pytest.mark.parametrize(
    (
        "student_access_mode",
        "is_storage_limit_reached",
        "expected_content_token_payload",
    ),
    [
        pytest.param(
            MaterialAccessMode.READ_ONLY,
            None,
            lfc(
                lambda classroom_material, student_user_id: ContentTokenPayloadSchema(
                    material_id=classroom_material.id,
                    ydoc_id=classroom_material.main_ydoc_id,
                    user_id=student_user_id,
                    can_upload_files=False,
                    can_read_files=True,
                    can_add_library_files=False,
                    ydoc_access_level=YDocAccessLevel.READ_ONLY,
                ),
            ),
            id="read_only-limit_not_checked",
        ),
        pytest.param(
            MaterialAccessMode.READ_WRITE,
            False,
            lfc(
                lambda classroom_material, student_user_id: ContentTokenPayloadSchema(
                    material_id=classroom_material.id,
                    ydoc_id=classroom_material.main_ydoc_id,
                    user_id=student_user_id,
                    can_upload_files=True,
                    can_read_files=True,
                    can_add_library_files=False,
                    ydoc_access_level=YDocAccessLevel.READ_WRITE,
                ),
            ),
            id="read_write-limit_not_reached",
        ),
        pytest.param(
            MaterialAccessMode.READ_WRITE,
            True,
            lfc(
                lambda classroom_material, student_user_id: ContentTokenPayloadSchema(
                    material_id=classroom_material.id,
                    ydoc_id=classroom_material.main_ydoc_id,
                    user_id=student_user_id,
                    can_upload_files=False,
                    can_read_files=True,
                    can_add_library_files=False,
                    ydoc_access_level=YDocAccessLevel.READ_ONLY,
                ),
            ),
            id="read_write-limit_reached",
        ),
    ],
)
async def test_classroom_material_storage_item_retrieving(
    active_session: ActiveSession,
    mock_stack: MockStack,
    tutor_user_id: int,
    student_client: TestClient,
    classroom_material: ClassroomMaterial,
    student_access_mode: MaterialAccessMode,
    is_storage_limit_reached: bool | None,
    expected_content_token_payload: ContentTokenPayloadSchema,
) -> None:
    storage_limit_mock = mock_stack.enter_async_mock(
        storage_svc,
        "has_owner_reached_storage_limit",
        return_value=bool(is_storage_limit_reached),
    )  # limiting is tested in test_storage_svc.py

    async with active_session() as session:
        session.add(classroom_material)
        classroom_material.student_access_mode = student_access_mode

    expected_content_token: str = content_token_provider.serialize_and_sign(
        expected_content_token_payload
    )

    assert_response(
        student_client.get(
            "/api/protected/content-service/roles/student"
            f"/classrooms/{classroom_material.classroom_id}"
            f"/materials/{classroom_material.id}/storage-item/"
        ),
        expected_json={
            "ydoc_id": classroom_material.main_ydoc_id,
            "content_token": expected_content_token,
        },
    )

    if is_storage_limit_reached is None:
        storage_limit_mock.assert_not_awaited()
    else:
        storage_limit_mock.assert_awaited_once_with(owner_id=tutor_user_id)


classroom_material_student_request_parametrization = pytest.mark.parametrize(
    "postfix",
    [
        pytest.param("/", id="retrieve"),
        pytest.param("/storage-item/", id="retrieve-storage-item"),
    ],
)


@classroom_material_student_request_parametrization
async def test_classroom_material_access_denied(
    active_session: ActiveSession,
    student_client: TestClient,
    classroom_material: ClassroomMaterial,
    postfix: str,
) -> None:
    student_access_mode = random.choice(
        [MaterialAccessMode.READ_WRITE, MaterialAccessMode.READ_ONLY]
    )

    async with active_session() as session:
        session.add(classroom_material)
        classroom_material.student_access_mode = student_access_mode

    other_classroom_id: int = random.randint(
        classroom_material.classroom_id + 1,
        classroom_material.classroom_id + 1000,
    )

    assert_response(
        student_client.get(
            "/api/protected/content-service/roles/student"
            f"/classrooms/{other_classroom_id}"
            f"/materials/{classroom_material.id}{postfix}"
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )


@classroom_material_student_request_parametrization
async def test_classroom_material_no_student_access(
    active_session: ActiveSession,
    student_client: TestClient,
    classroom_id: int,
    classroom_material: ClassroomMaterial,
    postfix: str,
) -> None:
    async with active_session() as session:
        session.add(classroom_material)
        classroom_material.student_access_mode = MaterialAccessMode.NO_ACCESS

    assert_response(
        student_client.get(
            "/api/protected/content-service/roles/student"
            f"/classrooms/{classroom_id}"
            f"/materials/{classroom_material.id}{postfix}"
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )


@classroom_material_student_request_parametrization
async def test_classroom_material_not_finding(
    student_client: TestClient,
    classroom_id: int,
    deleted_classroom_material_id: UUID,
    postfix: str,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/content-service/roles/student"
            f"/classrooms/{classroom_id}"
            f"/materials/{deleted_classroom_material_id}{postfix}"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Material not found"},
    )
