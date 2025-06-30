from uuid import UUID

import pytest
from faker import Faker
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.storage_sch import StorageAccessGroupKind, YDocAccessLevel
from app.storage.models.access_groups_db import AccessGroup
from app.storage.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.respx_ext import assert_last_httpx_request

pytestmark = pytest.mark.anyio


async def test_ydoc_creating(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    access_group: AccessGroup,
) -> None:
    ydoc_id = assert_response(
        internal_client.post(
            f"/internal/storage-service/access-groups/{access_group.id}/ydocs/",
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={"id": UUID},
    ).json()["id"]

    async with active_session():
        ydoc = await YDoc.find_first_by_id(ydoc_id)
        assert ydoc is not None
        assert ydoc.access_group_id == access_group.id


async def test_personal_ydoc_creating_missing_access_group(
    active_session: ActiveSession,
    authorized_internal_client: TestClient,
    proxy_auth_data: ProxyAuthData,
) -> None:
    ydoc_id = assert_response(
        authorized_internal_client.post(
            "/internal/storage-service/access-groups/personal/ydocs/",
        ),
        expected_code=201,
        expected_json={"id": UUID},
    ).json()["id"]

    async with active_session():
        ydoc = await YDoc.find_first_by_id(ydoc_id)
        assert ydoc is not None
        access_group: AccessGroup = await ydoc.awaitable_attrs.access_group
        assert ydoc.access_group_id == access_group.id
        assert access_group.kind == StorageAccessGroupKind.PERSONAL
        assert access_group.related_id == str(proxy_auth_data.user_id)

        await ydoc.delete()
        await access_group.delete()


async def test_personal_ydoc_creating_access_group_exists(
    active_session: ActiveSession,
    authorized_internal_client: TestClient,
    personal_access_group: AccessGroup,
    proxy_auth_data: ProxyAuthData,
) -> None:
    ydoc_id = assert_response(
        authorized_internal_client.post(
            "/internal/storage-service/access-groups/personal/ydocs/",
        ),
        expected_code=201,
        expected_json={"id": UUID},
    ).json()["id"]

    async with active_session():
        ydoc = await YDoc.find_first_by_id(ydoc_id)
        assert ydoc is not None
        assert ydoc.access_group_id == personal_access_group.id
        assert (
            await AccessGroup.count_by_kwargs(
                AccessGroup.id,
                kind=StorageAccessGroupKind.PERSONAL,
                related_id=str(proxy_auth_data.user_id),
            )
        ) == 1
        access_group: AccessGroup = await ydoc.awaitable_attrs.access_group
        assert access_group.kind == StorageAccessGroupKind.PERSONAL
        assert access_group.related_id == str(proxy_auth_data.user_id)

        await ydoc.delete()
        await access_group.delete()


async def test_ydoc_creating_access_group_not_found(
    faker: Faker,
    internal_client: TestClient,
    missing_access_group_id: UUID,
) -> None:
    assert_response(
        internal_client.post(
            f"/internal/storage-service/access-groups/{missing_access_group_id}/ydocs/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Access group not found"},
    )


async def test_ydoc_deleting(
    active_session: ActiveSession, internal_client: TestClient, ydoc: YDoc
) -> None:
    assert_nodata_response(
        internal_client.delete(f"/internal/storage-service/ydocs/{ydoc.id}/"),
    )

    async with active_session():
        assert (await YDoc.find_first_by_id(ydoc.id)) is None


@pytest.mark.parametrize(
    "access_level",
    [
        pytest.param(access_level, id=access_level.value)
        for access_level in YDocAccessLevel
    ],
)
async def test_board_channel_ydoc_access_level_retrieving(
    communities_respx_mock: MockRouter,
    proxy_auth_data: ProxyAuthData,
    authorized_internal_client: TestClient,
    board_channel_access_group: AccessGroup,
    board_channel_ydoc: YDoc,
    access_level: YDocAccessLevel,
) -> None:
    board_channel_access_level_mock = communities_respx_mock.get(
        path=f"/channels/{board_channel_access_group.related_id}/board/access-level/",
    ).respond(json=access_level.value)

    assert_response(
        authorized_internal_client.get(
            f"/internal/storage-service/ydocs/{board_channel_ydoc.id}/access-level/",
        ),
        expected_json=access_level.value,
    )

    assert_last_httpx_request(
        board_channel_access_level_mock,
        expected_headers={"X-Api-Key": settings.api_key, **proxy_auth_data.as_headers},
    )


async def test_personal_ydoc_access_level_retrieving_read_write(
    proxy_auth_data: ProxyAuthData,
    authorized_internal_client: TestClient,
    personal_ydoc: YDoc,
) -> None:
    assert_response(
        authorized_internal_client.get(
            f"/internal/storage-service/ydocs/{personal_ydoc.id}/access-level/",
        ),
        expected_json=YDocAccessLevel.READ_WRITE,
    )


async def test_personal_ydoc_access_level_retrieving_no_access(
    proxy_auth_data: ProxyAuthData,
    outsider_internal_client: TestClient,
    personal_ydoc: YDoc,
) -> None:
    assert_response(
        outsider_internal_client.get(
            f"/internal/storage-service/ydocs/{personal_ydoc.id}/access-level/",
        ),
        expected_json=YDocAccessLevel.NO_ACCESS,
    )


async def test_ydoc_access_level_retrieving_proxy_auth_required(
    internal_client: TestClient,
    ydoc: YDoc,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/storage-service/ydocs/{ydoc.id}/access-level/",
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Proxy auth required"},
    )


async def test_ydoc_content_retrieving(
    internal_client: TestClient,
    ydoc: YDoc,
) -> None:
    response = assert_response(
        internal_client.get(
            f"/internal/storage-service/ydocs/{ydoc.id}/content/",
        ),
        expected_json=None,
        expected_headers={
            "Content-Type": "application/octet-stream",
        },
    )
    assert response.content == ydoc.content


async def test_ydoc_content_updating(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    ydoc: YDoc,
) -> None:
    content: bytes = faker.binary(length=64)

    assert_nodata_response(
        internal_client.put(
            f"/internal/storage-service/ydocs/{ydoc.id}/content/",
            content=content,
            headers={"Content-Type": "application/octet-stream"},
        ),
    )

    async with active_session():
        updated_ydoc = await YDoc.find_first_by_id(ydoc.id)
        assert updated_ydoc is not None
        assert updated_ydoc.content == content


async def test_ydoc_content_clearing(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    ydoc: YDoc,
) -> None:
    assert_nodata_response(
        internal_client.delete(f"/internal/storage-service/ydocs/{ydoc.id}/content/"),
    )

    async with active_session():
        updated_ydoc = await YDoc.find_first_by_id(ydoc.id)
        assert updated_ydoc is not None
        assert updated_ydoc.content is None


@pytest.mark.parametrize(
    ("method", "with_content", "path"),
    [
        pytest.param("GET", False, "access-level", id="retrieve-access-level"),
        pytest.param("GET", False, "content", id="retrieve-content"),
        pytest.param("PUT", True, "content", id="update-content"),
        pytest.param("DELETE", False, "content", id="clear-content"),
    ],
)
async def test_ydoc_not_finding(
    faker: Faker,
    authorized_internal_client: TestClient,
    missing_ydoc_id: int,
    method: str,
    with_content: bool,
    path: str,
) -> None:
    assert_response(
        authorized_internal_client.request(
            method,
            f"/internal/storage-service/ydocs/{missing_ydoc_id}/{path}/",
            content=faker.binary(length=64) if with_content else None,
            headers=(
                {"Content-Type": "application/octet-stream"} if with_content else None
            ),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "YDoc not found"},
    )
