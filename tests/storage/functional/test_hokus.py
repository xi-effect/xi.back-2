from uuid import UUID

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.storage.models.access_groups_db import AccessGroup
from app.storage.models.hokus_db import Hoku
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response

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
