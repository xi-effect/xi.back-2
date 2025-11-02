import random

import pytest
from freezegun import freeze_time
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import storage_token_provider
from app.common.schemas.storage_sch import (
    StorageItemKind,
    StorageTokenPayloadSchema,
    YDocAccessLevel,
)
from app.materials.models.materials_db import ClassroomMaterial, MaterialAccessMode
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_material_retrieving(
    active_session: ActiveSession,
    student_client: TestClient,
    classroom_material: ClassroomMaterial,
    classroom_material_data: AnyJSON,
) -> None:
    student_access_mode = random.choice(
        [MaterialAccessMode.READ_WRITE, MaterialAccessMode.READ_ONLY]
    )

    async with active_session() as session:
        session.add(classroom_material)
        classroom_material.student_access_mode = student_access_mode

    assert_response(
        student_client.get(
            "/api/protected/material-service/roles/student"
            f"/classrooms/{classroom_material.classroom_id}"
            f"/materials/{classroom_material.id}/"
        ),
        expected_json={
            **classroom_material_data,
            "student_access_mode": student_access_mode,
        },
    )


@freeze_time()
@pytest.mark.parametrize(
    ("student_access_mode", "storage_token_payload"),
    [
        pytest.param(
            MaterialAccessMode.READ_ONLY,
            lfc(
                lambda access_group_id, user_id: StorageTokenPayloadSchema(
                    access_group_id=access_group_id,
                    user_id=user_id,
                    can_upload_files=False,
                    can_read_files=True,
                    ydoc_access_level=YDocAccessLevel.READ_ONLY,
                ),
                lf("classroom_material.access_group_id"),
                lf("student_user_id"),
            ),
            id=MaterialAccessMode.READ_ONLY.value,
        ),
        pytest.param(
            MaterialAccessMode.READ_WRITE,
            lfc(
                lambda access_group_id, user_id: StorageTokenPayloadSchema(
                    access_group_id=access_group_id,
                    user_id=user_id,
                    can_upload_files=True,
                    can_read_files=True,
                    ydoc_access_level=YDocAccessLevel.READ_WRITE,
                ),
                lf("classroom_material.access_group_id"),
                lf("student_user_id"),
            ),
            id=MaterialAccessMode.READ_WRITE.value,
        ),
    ],
)
async def test_material_storage_item_retrieving(
    active_session: ActiveSession,
    student_client: TestClient,
    classroom_material: ClassroomMaterial,
    student_access_mode: MaterialAccessMode,
    storage_token_payload: StorageTokenPayloadSchema,
) -> None:
    async with active_session() as session:
        session.add(classroom_material)
        classroom_material.student_access_mode = student_access_mode

    storage_token: str = storage_token_provider.serialize_and_sign(
        storage_token_payload
    )

    assert_response(
        student_client.get(
            "/api/protected/material-service/roles/student"
            f"/classrooms/{classroom_material.classroom_id}"
            f"/materials/{classroom_material.id}/storage-item/"
        ),
        expected_json={
            "kind": StorageItemKind.YDOC,
            "access_group_id": classroom_material.access_group_id,
            "ydoc_id": classroom_material.content_id,
            "storage_token": storage_token,
        },
    )


classroom_material_student_request_parametrization = pytest.mark.parametrize(
    "postfix",
    [
        pytest.param("/", id="retrieve"),
        pytest.param("/storage-item/", id="retrieve-storage-item"),
    ],
)


@classroom_material_student_request_parametrization
async def test_material_no_student_access(
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
            "/api/protected/material-service/roles/student"
            f"/classrooms/{classroom_id}"
            f"/materials/{classroom_material.id}{postfix}"
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )


@classroom_material_student_request_parametrization
async def test_material_access_denied(
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
            "/api/protected/material-service/roles/student"
            f"/classrooms/{other_classroom_id}"
            f"/materials/{classroom_material.id}{postfix}"
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )


@classroom_material_student_request_parametrization
async def test_material_not_finding(
    student_client: TestClient,
    classroom_id: int,
    deleted_classroom_material_id: int,
    postfix: str,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/material-service/roles/student"
            f"/classrooms/{classroom_id}"
            f"/materials/{deleted_classroom_material_id}{postfix}"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Material not found"},
    )
