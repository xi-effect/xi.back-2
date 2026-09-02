from uuid import UUID

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.common.config import content_token_provider
from app.common.schemas.content_sch import ContentTokenPayloadSchema, YDocAccessLevel
from app.common.utils.datetime import datetime_utc_now
from app.content.models.materials_db import ClassroomNoteMaterial
from app.content.models.ydocs_db import YDocContentKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_classroom_note_creation(
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
    classroom_id: int,
) -> None:
    response_json: AnyJSON = assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/note/storage-item/"
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={"ydoc_id": UUID, "content_token": str},
    ).json()

    async with active_session():
        classroom_note_material = await ClassroomNoteMaterial.find_first_by_kwargs(
            classroom_id=classroom_id,
        )
        assert classroom_note_material is not None
        assert_contains(classroom_note_material, {"updated_at": datetime_utc_now()})

        assert_contains(
            {
                "owner_id": classroom_note_material.main_ydoc.owner_id,
                "content_kind": classroom_note_material.main_ydoc.content_kind,
                "content": (
                    await classroom_note_material.main_ydoc.awaitable_attrs.content
                ),
                "size_bytes": classroom_note_material.main_ydoc.size_bytes,
                "created_at": classroom_note_material.main_ydoc.created_at,
                "updated_at": classroom_note_material.main_ydoc.updated_at,
            },
            {
                "owner_id": tutor_user_id,
                "content_kind": YDocContentKind.NOTE,
                "content": None,
                "size_bytes": 0,
                "created_at": datetime_utc_now(),
                "updated_at": datetime_utc_now(),
            },
        )

        expected_content_token_payload = ContentTokenPayloadSchema(
            material_id=classroom_note_material.id,
            ydoc_id=classroom_note_material.main_ydoc_id,
            user_id=tutor_user_id,
            can_upload_files=True,
            can_read_files=True,
            can_add_library_files=True,
            ydoc_access_level=YDocAccessLevel.READ_WRITE,
        )
        assert_contains(
            response_json,
            {
                "ydoc_id": classroom_note_material.main_ydoc_id,
                "content_token": content_token_provider.serialize_and_sign(
                    expected_content_token_payload
                ),
            },
        )

        await classroom_note_material.delete()
        await classroom_note_material.main_ydoc.delete()


async def test_classroom_note_creation_classroom_note_already_exists(
    tutor_client: TestClient,
    classroom_note_material: ClassroomNoteMaterial,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_note_material.classroom_id}/note/storage-item/"
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Classroom note already exists"},
    )


@freeze_time()
async def test_classroom_note_storage_item_retrieving(
    tutor_user_id: int,
    tutor_client: TestClient,
    classroom_note_material: ClassroomNoteMaterial,
) -> None:
    expected_content_token: str = content_token_provider.serialize_and_sign(
        ContentTokenPayloadSchema(
            material_id=classroom_note_material.id,
            ydoc_id=classroom_note_material.main_ydoc_id,
            user_id=tutor_user_id,
            can_upload_files=True,
            can_read_files=True,
            can_add_library_files=True,
            ydoc_access_level=YDocAccessLevel.READ_WRITE,
        )
    )

    assert_response(
        tutor_client.get(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_note_material.classroom_id}/note/storage-item/"
        ),
        expected_json={
            "ydoc_id": classroom_note_material.main_ydoc_id,
            "content_token": expected_content_token,
        },
    )


async def test_classroom_note_storage_item_retrieving_classroom_note_not_found(
    tutor_client: TestClient,
    classroom_id: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/note/storage-item/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom note not found"},
    )
