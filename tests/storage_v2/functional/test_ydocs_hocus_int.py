import pytest
from faker import Faker
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import storage_token_provider
from app.common.schemas.storage_sch import StorageTokenPayloadSchema
from app.storage_v2.models.access_groups_db import AccessGroupYDoc
from app.storage_v2.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.storage_v2 import factories

pytestmark = pytest.mark.anyio


@pytest.fixture()
def ydocs_access_storage_token_payload(
    authorized_user_id: int,
    access_group_ydoc: AccessGroupYDoc,
) -> StorageTokenPayloadSchema:
    return factories.StorageTokenPayloadFactory.build(
        access_group_id=access_group_ydoc.access_group_id,
        user_id=authorized_user_id,
        can_upload_files=True,
    )


@pytest.fixture()
def ydocs_access_storage_token(
    ydocs_access_storage_token_payload: StorageTokenPayloadSchema,
) -> str:
    return storage_token_provider.serialize_and_sign(ydocs_access_storage_token_payload)


async def test_ydoc_access_level_retrieving(
    authorized_internal_client: TestClient,
    access_group_ydoc: AccessGroupYDoc,
    ydocs_access_storage_token_payload: StorageTokenPayloadSchema,
    ydocs_access_storage_token: str,
) -> None:
    assert_response(
        authorized_internal_client.get(
            f"/internal/storage-service/v2/ydocs/{access_group_ydoc.ydoc_id}/access-level/",
            headers={"X-Storage-Token": ydocs_access_storage_token},
        ),
        expected_json=ydocs_access_storage_token_payload.ydoc_access_level,
    )


@pytest.mark.parametrize(
    "storage_token",
    [
        pytest.param(
            lfc(
                "storage_token_generator",
                lf("access_group_ydoc.access_group_id"),
                lf("outsider_user_id"),
            ),
            id="incorrect_user",
        ),
        pytest.param(
            lfc(
                "storage_token_generator",
                lf("missing_access_group_id"),
                lf("authorized_user_id"),
            ),
            id="missing_access_group",
        ),
        pytest.param(
            lfc("faker.password"),
            id="malformed_token",
        ),
    ],
)
async def test_ydoc_access_level_invalid_token(
    authorized_internal_client: TestClient,
    ydoc: YDoc,
    storage_token: str,
) -> None:
    assert_response(
        authorized_internal_client.get(
            f"/internal/storage-service/v2/ydocs/{ydoc.id}/access-level/",
            headers={"X-Storage-Token": storage_token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid storage token"},
    )


async def test_ydoc_access_level_retrieving_proxy_authorization_missing(
    internal_client: TestClient,
    access_group_ydoc: AccessGroupYDoc,
    ydocs_access_storage_token: str,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/storage-service/v2/ydocs/{access_group_ydoc.ydoc_id}/access-level/",
            headers={"X-Storage-Token": ydocs_access_storage_token},
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
            f"/internal/storage-service/v2/ydocs/{ydoc.id}/content/",
        ),
        expected_json=None,
        expected_headers={
            "Content-Type": "application/octet-stream",
        },
    ).content
    assert response_content == ydoc.content


async def test_ydoc_content_updating(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    ydoc: YDoc,
) -> None:
    content: bytes = faker.binary(length=64)

    assert_nodata_response(
        internal_client.put(
            f"/internal/storage-service/v2/ydocs/{ydoc.id}/content/",
            content=content,
            headers={"Content-Type": "application/octet-stream"},
        ),
    )

    async with active_session() as session:
        session.add(ydoc)
        await session.refresh(ydoc)
        assert ydoc.content == content


async def test_ydoc_content_clearing(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    ydoc: YDoc,
) -> None:
    assert_nodata_response(
        internal_client.delete(
            f"/internal/storage-service/v2/ydocs/{ydoc.id}/content/"
        ),
    )

    async with active_session() as session:
        session.add(ydoc)
        await session.refresh(ydoc)
        assert ydoc.content is None


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
    missing_ydoc_id: int,
    method: str,
    path: str,
    with_content: bool,
) -> None:
    assert_response(
        authorized_internal_client.request(
            method,
            f"/internal/storage-service/v2/ydocs/{missing_ydoc_id}/{path}/",
            content=faker.binary(length=64) if with_content else None,
            headers=(
                {"Content-Type": "application/octet-stream"} if with_content else None
            ),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "YDoc not found"},
    )
