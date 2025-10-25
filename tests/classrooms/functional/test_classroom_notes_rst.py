from uuid import uuid4

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.classroom_notes_db import ClassroomNote
from app.classrooms.models.classrooms_db import (
    AnyClassroom,
)
from app.common.config import settings, storage_token_provider
from app.common.schemas.storage_sch import (
    StorageItemKind,
    StorageTokenPayloadSchema,
    YDocAccessLevel,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.respx_ext import assert_last_httpx_request

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_classroom_note_creation(
    active_session: ActiveSession,
    storage_v2_respx_mock: MockRouter,
    tutor_user_id: int,
    tutor_client: TestClient,
    any_classroom: AnyClassroom,
) -> None:
    access_group_id = uuid4()
    ydoc_id = uuid4()

    create_access_group_mock = storage_v2_respx_mock.post("/access-groups/").respond(
        status_code=status.HTTP_201_CREATED, json={"id": str(access_group_id)}
    )
    create_ydoc_mock = storage_v2_respx_mock.post(
        f"/access-groups/{access_group_id}/ydocs/"
    ).respond(status_code=status.HTTP_201_CREATED, json={"id": str(ydoc_id)})

    storage_token_payload = StorageTokenPayloadSchema(
        access_group_id=access_group_id,
        user_id=tutor_user_id,
        can_upload_files=True,
        can_read_files=True,
        ydoc_access_level=YDocAccessLevel.READ_WRITE,
    )
    storage_token: str = storage_token_provider.serialize_and_sign(
        storage_token_payload
    )

    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor"
            f"/classrooms/{any_classroom.id}/note/storage-item/"
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            "kind": StorageItemKind.YDOC,
            "access_group_id": access_group_id,
            "ydoc_id": ydoc_id,
            "storage_token": storage_token,
        },
    )

    assert_last_httpx_request(
        create_access_group_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )
    assert_last_httpx_request(
        create_ydoc_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )

    async with active_session():
        classroom_note = await ClassroomNote.find_first_by_id(any_classroom.id)
        assert classroom_note is not None
        assert_contains(
            classroom_note,
            {
                "access_group_id": access_group_id,
                "ydoc_id": ydoc_id,
            },
        )
        await classroom_note.delete()


async def test_classroom_note_creation_classroom_note_already_exists(
    tutor_client: TestClient,
    classroom_note: ClassroomNote,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor"
            f"/classrooms/{classroom_note.classroom_id}/note/storage-item/"
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Classroom note already exists"},
    )


@freeze_time()
async def test_classroom_note_retrieving(
    tutor_user_id: int,
    tutor_client: TestClient,
    classroom_note: ClassroomNote,
) -> None:
    storage_token_payload = StorageTokenPayloadSchema(
        access_group_id=classroom_note.access_group_id,
        user_id=tutor_user_id,
        can_upload_files=True,
        can_read_files=True,
        ydoc_access_level=YDocAccessLevel.READ_WRITE,
    )
    storage_token: str = storage_token_provider.serialize_and_sign(
        storage_token_payload
    )

    assert_response(
        tutor_client.get(
            "/api/protected/classroom-service/roles/tutor"
            f"/classrooms/{classroom_note.classroom_id}/note/storage-item/"
        ),
        expected_json={
            "kind": StorageItemKind.YDOC,
            "access_group_id": classroom_note.access_group_id,
            "ydoc_id": classroom_note.ydoc_id,
            "storage_token": storage_token,
        },
    )


async def test_classroom_note_retrieving_classroom_note_not_found(
    tutor_client: TestClient,
    deleted_classroom_note_id: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/classroom-service/roles/tutor"
            f"/classrooms/{deleted_classroom_note_id}/note/storage-item/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom note not found"},
    )
