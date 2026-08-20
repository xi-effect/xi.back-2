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
from app.content.models.materials_db import PersonalMaterial
from app.content.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.content import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_personal_material_creation(
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
) -> None:
    input_data = factories.PersonalMaterialInputFactory.build_json()

    material_id: UUID = assert_response(
        tutor_client.post(
            "/api/protected/content-service/roles/tutor/personal-materials/",
            json=input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **input_data,
            "id": UUID,
            "access_kind": "personal",
            "updated_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        personal_material = await PersonalMaterial.find_first_by_id(material_id)
        assert personal_material is not None
        assert_contains(personal_material, {"tutor_id": tutor_user_id})

        assert_contains(
            {
                "owner_id": personal_material.main_ydoc.owner_id,
                "content_kind": personal_material.main_ydoc.content_kind,
                "content": await personal_material.main_ydoc.awaitable_attrs.content,
                "size_bytes": personal_material.main_ydoc.size_bytes,
                "created_at": personal_material.main_ydoc.created_at,
                "updated_at": personal_material.main_ydoc.updated_at,
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

        await personal_material.delete()
        await personal_material.main_ydoc.delete()


async def test_personal_material_retrieving(
    tutor_client: TestClient,
    personal_material: PersonalMaterial,
    personal_material_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/content-service/roles/tutor"
            f"/personal-materials/{personal_material.id}/"
        ),
        expected_json=personal_material_data,
    )


@freeze_time()
async def test_personal_material_storage_item_retrieving(
    tutor_user_id: int,
    tutor_client: TestClient,
    personal_material: PersonalMaterial,
) -> None:
    expected_content_token: str = content_token_provider.serialize_and_sign(
        ContentTokenPayloadSchema(
            material_id=personal_material.id,
            ydoc_id=personal_material.main_ydoc_id,
            user_id=tutor_user_id,
            can_upload_files=True,
            can_read_files=True,
            ydoc_access_level=YDocAccessLevel.READ_WRITE,
        )
    )

    assert_response(
        tutor_client.get(
            "/api/protected/content-service/roles/tutor"
            f"/personal-materials/{personal_material.id}/storage-item/"
        ),
        expected_json={
            "ydoc_id": personal_material.main_ydoc_id,
            "content_token": expected_content_token,
        },
    )


async def test_personal_material_updating(
    tutor_client: TestClient,
    personal_material: PersonalMaterial,
    personal_material_data: AnyJSON,
) -> None:
    patch_data = factories.PersonalMaterialPatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            "/api/protected/content-service/roles/tutor"
            f"/personal-materials/{personal_material.id}/",
            json=patch_data,
        ),
        expected_json={**personal_material_data, **patch_data},
    )


async def test_personal_material_deleting(
    active_session: ActiveSession,
    tutor_client: TestClient,
    personal_material: PersonalMaterial,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            "/api/protected/content-service/roles/tutor"
            f"/personal-materials/{personal_material.id}/"
        )
    )

    async with active_session():
        assert await PersonalMaterial.find_first_by_id(personal_material.id) is None
        assert await YDoc.find_first_by_id(personal_material.main_ydoc_id) is None


personal_material_request_parametrization = pytest.mark.parametrize(
    ("method", "postfix", "body_factory"),
    [
        pytest.param("GET", "/", None, id="retrieve"),
        pytest.param("GET", "/storage-item/", None, id="retrieve-storage-item"),
        pytest.param("PATCH", "/", factories.PersonalMaterialPatchFactory, id="update"),
        pytest.param("DELETE", "/", None, id="delete"),
    ],
)


@personal_material_request_parametrization
async def test_personal_material_access_denied(
    outsider_client: TestClient,
    personal_material: PersonalMaterial,
    method: str,
    postfix: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        outsider_client.request(
            method=method,
            url=(
                "/api/protected/content-service/roles/tutor"
                f"/personal-materials/{personal_material.id}{postfix}"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Material access denied"},
    )


@personal_material_request_parametrization
async def test_personal_material_not_finding(
    tutor_client: TestClient,
    deleted_personal_material_id: UUID,
    method: str,
    postfix: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=(
                "/api/protected/content-service/roles/tutor"
                f"/personal-materials/{deleted_personal_material_id}{postfix}"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Material not found"},
    )
