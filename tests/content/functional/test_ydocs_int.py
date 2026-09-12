import gzip
from typing import Any
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
            "Content-Encoding": "gzip",
        },
    ).content

    assert response_content == gzip.decompress(ydoc.path.read_bytes())


async def test_ydoc_content_retrieving_without_content(
    internal_client: TestClient,
    ydoc_without_content: YDoc,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/content-service/ydocs/{ydoc_without_content.id}/content/",
        ),
        expected_json=None,
        expected_headers={
            "Content-Type": "application/octet-stream",
            "Content-Encoding": None,
            "Content-Length": "0",
        },
    )


@freeze_time()
@pytest.mark.parametrize(
    "is_content_gzipped",
    [
        pytest.param(False, id="raw_content"),
        pytest.param(True, id="gzipped_content"),
    ],
)
async def test_ydoc_content_updating(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    personal_material: PersonalMaterial,
    is_content_gzipped: bool,
) -> None:
    content: bytes = faker.binary(length=64)
    request_headers = {"Content-Type": "application/octet-stream"}
    if is_content_gzipped:
        request_headers["Content-Encoding"] = "gzip"
        request_headers["X-Size-Bytes"] = str(len(content))

    assert_nodata_response(
        internal_client.put(
            f"/internal/content-service/ydocs/{personal_material.main_ydoc_id}/content/",
            content=gzip.compress(content) if is_content_gzipped else content,
            headers=request_headers,
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
                "content": gzip.decompress(main_ydoc.path.read_bytes()),
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

    assert not personal_material.main_ydoc.path.exists()

    async with active_session() as session:
        session.add(personal_material)
        await session.refresh(personal_material)
        assert_contains(personal_material, {"updated_at": datetime_utc_now()})

        main_ydoc = personal_material.main_ydoc
        await session.refresh(main_ydoc)
        assert_contains(
            main_ydoc,
            {"size_bytes": 0, "updated_at": datetime_utc_now()},
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
    ("method", "path", "with_content", "body_factory"),
    [
        pytest.param("GET", "access-level", False, None, id="retrieve-access-level"),
        pytest.param("GET", "content", False, None, id="retrieve-content"),
        pytest.param("PUT", "content", True, None, id="update-content"),
        pytest.param("DELETE", "content", False, None, id="clear-content"),
        pytest.param(
            "PUT",
            "content-meta",
            False,
            factories.YDocContentMetaInputFactory,
            id="update-content-meta",
        ),
    ],
)
async def test_ydoc_not_finding(
    faker: Faker,
    authorized_internal_client: TestClient,
    missing_ydoc_id: UUID,
    method: str,
    path: str,
    with_content: bool,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        authorized_internal_client.request(
            method,
            f"/internal/content-service/ydocs/{missing_ydoc_id}/{path}/",
            content=faker.binary(length=64) if with_content else None,
            json=body_factory and body_factory.build_json(),
            headers=(
                {"Content-Type": "application/octet-stream"} if with_content else None
            ),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "YDoc not found"},
    )
