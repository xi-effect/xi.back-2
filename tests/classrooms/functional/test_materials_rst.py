from typing import Any
from uuid import uuid4

import pytest
from freezegun import freeze_time
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.materials_db import Material
from app.common.config import settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.utils.datetime import datetime_utc_now
from tests.classrooms.factories import MaterialInputFactory, MaterialPatchFactory
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_material_creation(
    active_session: ActiveSession,
    storage_respx_mock: MockRouter,
    tutor_auth_data: ProxyAuthData,
    tutor_client: TestClient,
) -> None:
    ydoc_id = str(uuid4())

    storage_bridge_mock = storage_respx_mock.post(
        "/access-groups/personal/ydocs/"
    ).respond(status_code=status.HTTP_201_CREATED, json={"id": ydoc_id})

    material_input_data = MaterialInputFactory.build_json()
    material_id: int = assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor/materials/",
            json=material_input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **material_input_data,
            "id": int,
            "created_at": datetime_utc_now(),
            "last_opened_at": datetime_utc_now(),
            "updated_at": datetime_utc_now(),
            "ydoc_id": ydoc_id,
        },
    ).json()["id"]

    assert_last_httpx_request(
        storage_bridge_mock,
        expected_headers={**tutor_auth_data.as_headers, "X-Api-Key": settings.api_key},
    )

    async with active_session():
        material = await Material.find_first_by_id(material_id)
        assert material is not None
        assert material.tutor_id == tutor_auth_data.user_id
        await material.delete()


@freeze_time()
async def test_material_retrieving(
    tutor_client: TestClient,
    material_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            f"/api/protected/classroom-service/roles/tutor/materials/{material_data["id"]}/"
        ),
        expected_json={**material_data, "last_opened_at": datetime_utc_now()},
    )


@freeze_time()
async def test_material_updating(
    tutor_client: TestClient,
    material_data: AnyJSON,
) -> None:
    patch_material_data = MaterialPatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            f"/api/protected/classroom-service/roles/tutor/materials/{material_data["id"]}/",
            json=patch_material_data,
        ),
        expected_json={
            **material_data,
            **patch_material_data,
            "updated_at": datetime_utc_now(),
        },
    )


async def test_material_deleting(
    active_session: ActiveSession,
    storage_respx_mock: MockRouter,
    tutor_auth_data: ProxyAuthData,
    tutor_client: TestClient,
    material: Material,
) -> None:
    storage_bridge_mock = storage_respx_mock.delete(
        f"/ydocs/{material.ydoc_id}/"
    ).respond(status_code=status.HTTP_204_NO_CONTENT)

    assert_nodata_response(
        tutor_client.delete(
            f"/api/protected/classroom-service/roles/tutor/materials/{material.id}/"
        )
    )

    assert_last_httpx_request(
        storage_bridge_mock, expected_headers={"X-Api-Key": settings.api_key}
    )
    async with active_session():
        assert await Material.find_first_by_id(material.id) is None


material_requests_params = [
    pytest.param("GET", None, id="retrieve"),
    pytest.param("PATCH", MaterialPatchFactory, id="update"),
    pytest.param("DELETE", None, id="delete"),
]


@pytest.mark.parametrize(("method", "body_factory"), material_requests_params)
async def test_material_not_finding(
    tutor_client: TestClient,
    deleted_material_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=f"/api/protected/classroom-service/roles/tutor/materials/{deleted_material_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Material not found"},
    )


@pytest.mark.parametrize(("method", "body_factory"), material_requests_params)
async def test_material_access_denied(
    outsider_client: TestClient,
    material: Material,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        outsider_client.request(
            method=method,
            url=f"/api/protected/classroom-service/roles/tutor/materials/{material.id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )
