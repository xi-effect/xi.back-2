from collections.abc import AsyncIterator
from random import randint
from typing import Any
from uuid import UUID

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.common.config import content_token_provider
from app.common.schemas.content_sch import ContentTokenPayloadSchema, YDocAccessLevel
from app.common.utils.datetime import datetime_utc_now
from app.content.models.files_db import File
from app.content.models.materials_db import ClassroomMaterial, Material
from app.content.models.ydoc_files_db import YDocFile
from app.content.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.content import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_classroom_material_creation(
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
    classroom_id: int,
) -> None:
    input_data = factories.ClassroomMaterialInputFactory.build_json()

    material_id: UUID = assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/materials/",
            json=input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **input_data,
            "id": UUID,
            "access_kind": "classroom",
            "classroom_id": classroom_id,
            "updated_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        classroom_material = await ClassroomMaterial.find_first_by_id(material_id)
        assert classroom_material is not None

        assert_contains(
            {
                "owner_id": classroom_material.main_ydoc.owner_id,
                "content_kind": classroom_material.main_ydoc.content_kind,
                "content": await classroom_material.main_ydoc.awaitable_attrs.content,
                "size_bytes": classroom_material.main_ydoc.size_bytes,
                "created_at": classroom_material.main_ydoc.created_at,
                "updated_at": classroom_material.main_ydoc.updated_at,
            },
            {
                "owner_id": tutor_user_id,
                "content_kind": input_data["content_kind"],
                "content": None,
                "size_bytes": 0,
                "created_at": datetime_utc_now(),
                "updated_at": datetime_utc_now(),
            },
        )

        await classroom_material.delete()
        await classroom_material.main_ydoc.delete()


@pytest.fixture()
async def any_material_ydoc_file(
    active_session: ActiveSession,
    file: File,
    any_material: Material,
) -> AsyncIterator[YDocFile]:
    async with active_session():
        any_material_ydoc_file = await YDocFile.create(
            ydoc_id=any_material.main_ydoc_id,
            file_id=file.id,
        )

    yield any_material_ydoc_file

    async with active_session():
        await YDocFile.delete_by_kwargs(
            ydoc_id=any_material_ydoc_file.ydoc_id,
            file_id=any_material_ydoc_file.file_id,
        )


@freeze_time()
async def test_material_to_classroom_duplication(
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
    classroom_id: int,
    any_material: Material,
    any_material_ydoc_file: YDocFile,
) -> None:
    input_data = factories.ClassroomMaterialDuplicateInputFactory.build_json()
    target_classroom_id: int = randint(classroom_id + 1, classroom_id + 1000)

    material_id: UUID = assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{target_classroom_id}/material-duplicates/",
            json={**input_data, "source_id": str(any_material.id)},
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **input_data,
            "id": UUID,
            "access_kind": "classroom",
            "classroom_id": target_classroom_id,
            "content_kind": any_material.content_kind,
            "updated_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        classroom_material = await ClassroomMaterial.find_first_by_id(material_id)
        assert classroom_material is not None

        assert_contains(
            {
                "owner_id": classroom_material.main_ydoc.owner_id,
                "content_kind": classroom_material.main_ydoc.content_kind,
                "content": await classroom_material.main_ydoc.awaitable_attrs.content,
                "size_bytes": classroom_material.main_ydoc.size_bytes,
                "created_at": classroom_material.main_ydoc.created_at,
                "updated_at": classroom_material.main_ydoc.updated_at,
            },
            {
                "owner_id": tutor_user_id,
                "content_kind": any_material.content_kind,
                "content": any_material.main_ydoc.content,
                "size_bytes": any_material.main_ydoc.size_bytes,
                "created_at": datetime_utc_now(),
                "updated_at": datetime_utc_now(),
            },
        )

        assert (
            await YDocFile.find_first_by_ids(
                ydoc_id=classroom_material.main_ydoc_id,
                file_id=any_material_ydoc_file.file_id,
            )
            is not None
        )

        await classroom_material.delete()
        await classroom_material.main_ydoc.delete()


async def test_material_to_classroom_duplication_material_access_denied(
    outsider_client: TestClient,
    classroom_id: int,
    any_material: Material,
) -> None:
    assert_response(
        outsider_client.post(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/material-duplicates/",
            json={
                **factories.ClassroomMaterialDuplicateInputFactory.build_json(),
                "source_id": str(any_material.id),
            },
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )


async def test_material_to_classroom_duplication_material_not_found(
    tutor_client: TestClient,
    classroom_id: int,
    deleted_any_material_id: UUID,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_id}/material-duplicates/",
            json={
                **factories.ClassroomMaterialDuplicateInputFactory.build_json(),
                "source_id": str(deleted_any_material_id),
            },
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Material not found"},
    )


async def test_classroom_material_retrieving(
    tutor_client: TestClient,
    classroom_material: ClassroomMaterial,
    classroom_material_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_material.classroom_id}"
            f"/materials/{classroom_material.id}/"
        ),
        expected_json=classroom_material_data,
    )


@freeze_time()
async def test_classroom_material_storage_item_retrieving(
    tutor_user_id: int,
    tutor_client: TestClient,
    classroom_material: ClassroomMaterial,
) -> None:
    expected_content_token: str = content_token_provider.serialize_and_sign(
        ContentTokenPayloadSchema(
            material_id=classroom_material.id,
            ydoc_id=classroom_material.main_ydoc_id,
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
            f"/classrooms/{classroom_material.classroom_id}"
            f"/materials/{classroom_material.id}/storage-item/"
        ),
        expected_json={
            "ydoc_id": classroom_material.main_ydoc_id,
            "content_token": expected_content_token,
        },
    )


async def test_classroom_material_updating(
    tutor_client: TestClient,
    classroom_material: ClassroomMaterial,
    classroom_material_data: AnyJSON,
) -> None:
    patch_data = factories.ClassroomMaterialPatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_material.classroom_id}"
            f"/materials/{classroom_material.id}/",
            json=patch_data,
        ),
        expected_json={**classroom_material_data, **patch_data},
    )


async def test_classroom_material_deleting(
    active_session: ActiveSession,
    tutor_client: TestClient,
    classroom_material: ClassroomMaterial,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            "/api/protected/content-service/roles/tutor"
            f"/classrooms/{classroom_material.classroom_id}"
            f"/materials/{classroom_material.id}/"
        )
    )

    async with active_session():
        assert await ClassroomMaterial.find_first_by_id(classroom_material.id) is None
        assert await YDoc.find_first_by_id(classroom_material.main_ydoc_id) is None


classroom_material_tutor_request_parametrization = pytest.mark.parametrize(
    ("method", "postfix", "body_factory"),
    [
        pytest.param("GET", "/", None, id="retrieve"),
        pytest.param("GET", "/storage-item/", None, id="retrieve-storage-item"),
        pytest.param(
            "PATCH", "/", factories.ClassroomMaterialPatchFactory, id="update"
        ),
        pytest.param("DELETE", "/", None, id="delete"),
    ],
)


@classroom_material_tutor_request_parametrization
async def test_classroom_material_access_denied(
    tutor_client: TestClient,
    classroom_material: ClassroomMaterial,
    method: str,
    postfix: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    other_classroom_id: int = randint(
        classroom_material.classroom_id + 1,
        classroom_material.classroom_id + 1000,
    )

    assert_response(
        tutor_client.request(
            method=method,
            url=(
                "/api/protected/content-service/roles/tutor"
                f"/classrooms/{other_classroom_id}"
                f"/materials/{classroom_material.id}{postfix}"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )


@classroom_material_tutor_request_parametrization
async def test_classroom_material_not_finding(
    tutor_client: TestClient,
    classroom_id: int,
    deleted_classroom_material_id: UUID,
    method: str,
    postfix: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=(
                "/api/protected/content-service/roles/tutor"
                f"/classrooms/{classroom_id}"
                f"/materials/{deleted_classroom_material_id}{postfix}"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Material not found"},
    )
