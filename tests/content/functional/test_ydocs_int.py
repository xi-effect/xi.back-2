from typing import Any
from uuid import UUID

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import content_token_provider
from app.common.schemas.content_sch import ContentTokenPayloadSchema
from app.common.utils.datetime import datetime_utc_now
from app.content.models.materials_db import PersonalMaterial
from app.content.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.content import factories

pytestmark = pytest.mark.anyio


@pytest.fixture()
def ydoc_access_content_token_payload(
    authorized_user_id: int,
    material_id: UUID,
    ydoc: YDoc,
) -> ContentTokenPayloadSchema:
    return factories.ContentTokenPayloadFactory.build(
        material_id=material_id,
        ydoc_id=ydoc.id,
        user_id=authorized_user_id,
        can_upload_files=True,
    )


@pytest.fixture()
def ydoc_access_content_token(
    ydoc_access_content_token_payload: ContentTokenPayloadSchema,
) -> str:
    return content_token_provider.serialize_and_sign(ydoc_access_content_token_payload)


async def test_ydoc_access_level_retrieving(
    authorized_internal_client: TestClient,
    ydoc: YDoc,
    ydoc_access_content_token_payload: ContentTokenPayloadSchema,
    ydoc_access_content_token: str,
) -> None:
    assert_response(
        authorized_internal_client.get(
            f"/internal/content-service/ydocs/{ydoc.id}/access-level/",
            headers={"X-Content-Token": ydoc_access_content_token},
        ),
        expected_json=ydoc_access_content_token_payload.ydoc_access_level,
    )


@pytest.mark.parametrize(
    ("content_token", "ydoc_id"),
    [
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("ydoc.id"),
                lf("outsider_user_id"),
            ),
            lf("ydoc.id"),
            id="incorrect_user",
        ),
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("ydoc.id"),
                lf("authorized_user_id"),
            ),
            lf("other_ydoc.id"),
            id="wrong_ydoc",
        ),
        pytest.param(
            lfc("faker.password"),
            lf("ydoc.id"),
            id="malformed_token",
        ),
    ],
)
async def test_ydoc_access_level_invalid_token(
    authorized_internal_client: TestClient,
    content_token: str,
    ydoc_id: UUID,
) -> None:
    assert_response(
        authorized_internal_client.get(
            f"/internal/content-service/ydocs/{ydoc_id}/access-level/",
            headers={"X-Content-Token": content_token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid content token"},
    )


async def test_ydoc_access_level_retrieving_proxy_authorization_missing(
    internal_client: TestClient,
    ydoc: YDoc,
    ydoc_access_content_token: str,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/content-service/ydocs/{ydoc.id}/access-level/",
            headers={"X-Content-Token": ydoc_access_content_token},
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Proxy auth required"},
    )


@freeze_time()
async def test_ydoc_content_meta_updating(
    active_session: ActiveSession,
    internal_client: TestClient,
    personal_material: PersonalMaterial,
) -> None:
    input_data = factories.YDocContentMetaInputFactory.build_json()

    assert_nodata_response(
        internal_client.put(
            f"/internal/content-service/ydocs/{personal_material.main_ydoc_id}/content-meta/",
            json=input_data,
        ),
    )

    async with active_session() as session:
        session.add(personal_material)
        await session.refresh(personal_material)
        assert_contains(personal_material, {"updated_at": datetime_utc_now()})

        await session.refresh(personal_material.main_ydoc)
        assert_contains(
            personal_material.main_ydoc,
            {**input_data, "updated_at": datetime_utc_now()},
        )


@pytest.mark.parametrize(
    ("method", "path", "body_factory"),
    [
        pytest.param("GET", "access-level", None, id="retrieve-access-level"),
        pytest.param(
            "PUT",
            "content-meta",
            factories.YDocContentMetaInputFactory,
            id="update-content-meta",
        ),
    ],
)
async def test_ydoc_not_finding(
    authorized_internal_client: TestClient,
    missing_ydoc_id: UUID,
    method: str,
    path: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        authorized_internal_client.request(
            method,
            f"/internal/content-service/ydocs/{missing_ydoc_id}/{path}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "YDoc not found"},
    )
