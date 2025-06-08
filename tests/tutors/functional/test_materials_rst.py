from typing import Any

import pytest
from freezegun import freeze_time
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.tutors.models.materials_db import Material
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.tutors.factories import MaterialInputFactory, MaterialPatchFactory

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_material_creation(
    active_session: ActiveSession,
    tutor_client: TestClient,
    tutor_user_id: int,
) -> None:
    material_input_data = MaterialInputFactory.build_json()
    material_id: int = assert_response(
        tutor_client.post(
            "/api/protected/tutor-service/materials/",
            json=material_input_data,
        ),
        expected_code=201,
        expected_json={
            **material_input_data,
            "id": int,
            "created_at": datetime_utc_now(),
            "last_opened_at": datetime_utc_now(),
            "updated_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        material = await Material.find_first_by_id(material_id)
        assert material is not None
        assert material.tutor_id == tutor_user_id
        await material.delete()


@freeze_time()
async def test_material_retrieving(
    tutor_client: TestClient,
    material_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            f"/api/protected/tutor-service/materials/{material_data["id"]}/"
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
            f"/api/protected/tutor-service/materials/{material_data["id"]}/",
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
    tutor_client: TestClient,
    material: Material,
) -> None:
    assert_nodata_response(
        tutor_client.delete(f"/api/protected/tutor-service/materials/{material.id}/")
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
            url=f"/api/protected/tutor-service/materials/{deleted_material_id}/",
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
            url=f"/api/protected/tutor-service/materials/{material.id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )
