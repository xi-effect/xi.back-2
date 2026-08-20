from uuid import UUID

import pytest
from faker import Faker
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


async def test_ydoc_content_retrieving(
    internal_client: TestClient,
    ydoc: YDoc,
) -> None:
    response_content: bytes = assert_response(
        internal_client.get(
            f"/internal/content-service/ydocs/{ydoc.id}/content/",
        ),
        expected_json=None,
        expected_headers={
            "Content-Type": "application/octet-stream",
        },
    ).content
    assert response_content == ydoc.content


@freeze_time()
async def test_ydoc_content_updating(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    personal_material: PersonalMaterial,
) -> None:
    content: bytes = faker.binary(length=64)

    assert_nodata_response(
        internal_client.put(
            f"/internal/content-service/ydocs/{personal_material.main_ydoc_id}/content/",
            content=content,
            headers={"Content-Type": "application/octet-stream"},
        ),
    )

    async with active_session() as session:
        session.add(personal_material)
        await session.refresh(personal_material)
        assert_contains(personal_material, {"updated_at": datetime_utc_now()})

        main_ydoc = personal_material.main_ydoc
        await session.refresh(main_ydoc)
        assert_contains(
            {
                "content": await main_ydoc.awaitable_attrs.content,
                "size_bytes": main_ydoc.size_bytes,
                "updated_at": main_ydoc.updated_at,
            },
            {
                "content": content,
                "size_bytes": len(content),
                "updated_at": datetime_utc_now(),
            },
        )


@freeze_time()
async def test_ydoc_content_clearing(
    active_session: ActiveSession,
    internal_client: TestClient,
    personal_material: PersonalMaterial,
) -> None:
    assert_nodata_response(
        internal_client.delete(
            f"/internal/content-service/ydocs/{personal_material.main_ydoc_id}/content/"
        ),
    )

    async with active_session() as session:
        session.add(personal_material)
        await session.refresh(personal_material)
        assert_contains(personal_material, {"updated_at": datetime_utc_now()})

        main_ydoc = personal_material.main_ydoc
        await session.refresh(main_ydoc)
        assert_contains(
            {
                "content": await main_ydoc.awaitable_attrs.content,
                "size_bytes": main_ydoc.size_bytes,
                "updated_at": main_ydoc.updated_at,
            },
            {
                "content": None,
                "size_bytes": 0,
                "updated_at": datetime_utc_now(),
            },
        )


@pytest.mark.parametrize(
    ("method", "path", "with_content"),
    [
        pytest.param("GET", "access-level", False, id="retrieve-access-level"),
        pytest.param("GET", "content", False, id="retrieve-content"),
        pytest.param("PUT", "content", True, id="update-content"),
        pytest.param("DELETE", "content", False, id="clear-content"),
    ],
)
async def test_ydoc_not_finding(
    faker: Faker,
    authorized_internal_client: TestClient,
    missing_ydoc_id: UUID,
    method: str,
    path: str,
    with_content: bool,
) -> None:
    assert_response(
        authorized_internal_client.request(
            method,
            f"/internal/content-service/ydocs/{missing_ydoc_id}/{path}/",
            content=faker.binary(length=64) if with_content else None,
            headers=(
                {"Content-Type": "application/octet-stream"} if with_content else None
            ),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "YDoc not found"},
    )
