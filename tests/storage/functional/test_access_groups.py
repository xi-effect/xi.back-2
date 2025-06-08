from uuid import UUID

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.storage.models.access_groups_db import AccessGroup
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_access_group_creation(
    active_session: ActiveSession,
    internal_client: TestClient,
    access_group_data: AnyJSON,
) -> None:
    access_group_id = assert_response(
        internal_client.post(
            "/internal/storage-service/access-groups/",
            json=access_group_data,
        ),
        expected_code=201,
        expected_json={**access_group_data, "id": UUID},
    ).json()["id"]

    async with active_session():
        access_group = await AccessGroup.find_first_by_id(access_group_id)
        assert access_group is not None


async def test_access_group_deleting(
    active_session: ActiveSession,
    internal_client: TestClient,
    access_group: AccessGroup,
) -> None:
    assert_nodata_response(
        internal_client.delete(
            f"/internal/storage-service/access-groups/{access_group.id}",
        ),
    )

    async with active_session():
        assert (await AccessGroup.find_first_by_id(access_group.id)) is None


async def test_access_group_deleting_access_group_not_found(
    internal_client: TestClient,
    missing_access_group_id: UUID,
) -> None:
    assert_response(
        internal_client.delete(
            f"/internal/storage-service/access-groups/{missing_access_group_id}",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Access group not found"},
    )
