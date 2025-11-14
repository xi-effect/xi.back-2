from typing import Any
from uuid import uuid4

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings, storage_token_provider
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.storage_sch import (
    StorageItemKind,
    StorageTokenPayloadSchema,
    YDocAccessLevel,
)
from app.common.utils.datetime import datetime_utc_now
from app.materials.models.materials_db import TutorMaterial
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.materials import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_material_creation(
    active_session: ActiveSession,
    storage_v2_respx_mock: MockRouter,
    tutor_user_id: int,
    tutor_client: TestClient,
) -> None:
    access_group_id = uuid4()
    main_ydoc_id = uuid4()

    create_access_group_mock = storage_v2_respx_mock.post("/access-groups/").respond(
        status_code=status.HTTP_201_CREATED,
        json={"id": str(access_group_id), "main_ydoc_id": str(main_ydoc_id)},
    )

    input_data = factories.TutorMaterialInputFactory.build_json()
    material_id: int = assert_response(
        tutor_client.post(
            "/api/protected/material-service/roles/tutor/materials/",
            json=input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **input_data,
            "id": int,
            "created_at": datetime_utc_now(),
            "updated_at": datetime_utc_now(),
        },
    ).json()["id"]

    assert_last_httpx_request(
        create_access_group_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )

    async with active_session():
        tutor_material = await TutorMaterial.find_first_by_id(material_id)
        assert tutor_material is not None
        assert_contains(
            tutor_material,
            {
                "tutor_id": tutor_user_id,
                "access_group_id": access_group_id,
                "content_id": main_ydoc_id,
            },
        )
        await tutor_material.delete()


async def test_material_retrieving(
    tutor_client: TestClient,
    tutor_material: TutorMaterial,
    tutor_material_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/material-service/roles/tutor"
            f"/materials/{tutor_material.id}/"
        ),
        expected_json=tutor_material_data,
    )


@freeze_time()
async def test_material_storage_item_retrieving(
    tutor_user_id: int,
    tutor_client: TestClient,
    tutor_material: TutorMaterial,
    tutor_material_data: AnyJSON,
) -> None:
    storage_token_payload = StorageTokenPayloadSchema(
        access_group_id=tutor_material.access_group_id,
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
            "/api/protected/material-service/roles/tutor"
            f"/materials/{tutor_material.id}/storage-item/"
        ),
        expected_json={
            "kind": StorageItemKind.YDOC,
            "access_group_id": tutor_material.access_group_id,
            "ydoc_id": tutor_material.content_id,
            "storage_token": storage_token,
        },
    )


@freeze_time()
async def test_material_updating(
    tutor_client: TestClient,
    tutor_material: TutorMaterial,
    tutor_material_data: AnyJSON,
) -> None:
    patch_data = factories.TutorMaterialPatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            "/api/protected/material-service/roles/tutor"
            f"/materials/{tutor_material.id}/",
            json=patch_data,
        ),
        expected_json={
            **tutor_material_data,
            **patch_data,
            "updated_at": datetime_utc_now(),
        },
    )


async def test_material_deleting(
    active_session: ActiveSession,
    storage_v2_respx_mock: MockRouter,
    tutor_auth_data: ProxyAuthData,
    tutor_client: TestClient,
    tutor_material: TutorMaterial,
) -> None:
    delete_access_group_mock = storage_v2_respx_mock.delete(
        f"/access-groups/{tutor_material.access_group_id}/"
    ).respond(status_code=status.HTTP_204_NO_CONTENT)

    assert_nodata_response(
        tutor_client.delete(
            "/api/protected/material-service/roles/tutor"
            f"/materials/{tutor_material.id}/"
        )
    )

    assert_last_httpx_request(
        delete_access_group_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )
    async with active_session():
        assert await TutorMaterial.find_first_by_id(tutor_material.id) is None


tutor_material_request_parametrization = pytest.mark.parametrize(
    ("method", "postfix", "body_factory"),
    [
        pytest.param("GET", "/", None, id="retrieve"),
        pytest.param("GET", "/storage-item/", None, id="retrieve-storage-item"),
        pytest.param("PATCH", "/", factories.TutorMaterialPatchFactory, id="update"),
        pytest.param("DELETE", "/", None, id="delete"),
    ],
)


@tutor_material_request_parametrization
async def test_material_not_finding(
    tutor_client: TestClient,
    deleted_tutor_material_id: int,
    method: str,
    postfix: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=(
                "/api/protected/material-service/roles/tutor"
                f"/materials/{deleted_tutor_material_id}{postfix}"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Material not found"},
    )


@tutor_material_request_parametrization
async def test_material_access_denied(
    outsider_client: TestClient,
    tutor_material: TutorMaterial,
    method: str,
    postfix: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        outsider_client.request(
            method=method,
            url=(
                "/api/protected/material-service/roles/tutor"
                f"/materials/{tutor_material.id}{postfix}"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )
