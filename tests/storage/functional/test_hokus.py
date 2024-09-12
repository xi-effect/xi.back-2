from uuid import UUID

import pytest
from faker import Faker
from respx import MockRouter
from starlette.testclient import TestClient

from app.common.access import AccessLevel
from app.common.config import API_KEY
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.storage.models.access_groups_db import AccessGroup
from app.storage.models.hokus_db import Hoku
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.respx_ext import assert_last_httpx_request

pytestmark = pytest.mark.anyio


async def test_hoku_creating(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    access_group: AccessGroup,
) -> None:
    hoku_id = assert_response(
        internal_client.post(
            f"/internal/storage-service/access-groups/{access_group.id}/hokus/",
        ),
        expected_code=201,
        expected_json={"id": UUID},
    ).json()["id"]

    async with active_session():
        hoku = await Hoku.find_first_by_id(hoku_id)
        assert hoku is not None
        assert hoku.access_group_id == access_group.id


async def test_hoku_creating_access_group_not_found(
    faker: Faker,
    internal_client: TestClient,
    missing_access_group_id: UUID,
) -> None:
    assert_response(
        internal_client.post(
            f"/internal/storage-service/access-groups/{missing_access_group_id}/hokus/",
        ),
        expected_code=404,
        expected_json={"detail": "Access group not found"},
    )


@pytest.mark.parametrize(
    "access_level",
    [pytest.param(access_level, id=access_level.value) for access_level in AccessLevel],
)
async def test_hoku_access_level_retrieving(
    communities_respx_mock: MockRouter,
    proxy_auth_data: ProxyAuthData,
    authorized_internal_client: TestClient,
    access_group: AccessGroup,
    hoku: Hoku,
    access_level: AccessLevel,
) -> None:
    board_channel_access_level_mock = communities_respx_mock.get(
        path=f"/channels/{access_group.related_id}/board/access-level/",
    ).respond(json=access_level.value)

    assert_response(
        authorized_internal_client.get(
            f"/internal/storage-service/hokus/{hoku.id}/access-level/",
        ),
        expected_json=access_level.value,
    )

    assert_last_httpx_request(
        board_channel_access_level_mock,
        expected_headers={"X-Api-Key": API_KEY, **proxy_auth_data.as_headers},
    )


async def test_hoku_access_level_retrieving_proxy_auth_required(
    internal_client: TestClient,
    hoku: Hoku,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/storage-service/hokus/{hoku.id}/access-level/",
        ),
        expected_code=407,
        expected_json={"detail": "Proxy auth required"},
    )


async def test_hoku_content_retrieving(
    internal_client: TestClient,
    hoku: Hoku,
) -> None:
    response = assert_response(
        internal_client.get(
            f"/internal/storage-service/hokus/{hoku.id}/content/",
        ),
        expected_json=None,
        expected_headers={
            "Content-Type": "application/octet-stream",
        },
    )
    assert response.content == hoku.content


async def test_hoku_content_updating(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    hoku: Hoku,
) -> None:
    content: bytes = faker.binary(length=64)

    assert_nodata_response(
        internal_client.put(
            f"/internal/storage-service/hokus/{hoku.id}/content/",
            content=content,
            headers={"Content-Type": "application/octet-stream"},
        ),
    )

    async with active_session():
        updated_hoku = await Hoku.find_first_by_id(hoku.id)
        assert updated_hoku is not None
        assert updated_hoku.content == content


async def test_hoku_content_clearing(
    faker: Faker,
    active_session: ActiveSession,
    internal_client: TestClient,
    hoku: Hoku,
) -> None:
    assert_nodata_response(
        internal_client.delete(f"/internal/storage-service/hokus/{hoku.id}/content/"),
    )

    async with active_session():
        updated_hoku = await Hoku.find_first_by_id(hoku.id)
        assert updated_hoku is not None
        assert updated_hoku.content is None


@pytest.mark.parametrize(
    ("method", "with_content", "path"),
    [
        pytest.param("GET", False, "access-level", id="retrieve-access-level"),
        pytest.param("GET", False, "content", id="retrieve-content"),
        pytest.param("PUT", True, "content", id="update-content"),
        pytest.param("DELETE", False, "content", id="clear-content"),
    ],
)
async def test_hoku_not_finding(
    faker: Faker,
    authorized_internal_client: TestClient,
    missing_hoku_id: int,
    method: str,
    with_content: bool,
    path: str,
) -> None:
    assert_response(
        authorized_internal_client.request(
            method,
            f"/internal/storage-service/hokus/{missing_hoku_id}/{path}/",
            content=faker.binary(length=64) if with_content else None,
            headers=(
                {"Content-Type": "application/octet-stream"} if with_content else None
            ),
        ),
        expected_code=404,
        expected_json={"detail": "Hoku not found"},
    )
