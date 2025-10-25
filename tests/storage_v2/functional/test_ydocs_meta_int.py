from uuid import UUID

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.storage_v2.models.access_groups_db import AccessGroup, AccessGroupYDoc
from app.storage_v2.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


async def test_ydoc_creating(
    active_session: ActiveSession,
    internal_client: TestClient,
    access_group: AccessGroup,
) -> None:
    ydoc_id: UUID = assert_response(
        internal_client.post(
            f"/internal/storage-service/v2/access-groups/{access_group.id}/ydocs/",
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={"id": UUID},
    ).json()["id"]

    async with active_session():
        access_group_ydoc = await AccessGroupYDoc.find_by_ids(
            access_group_id=access_group.id,
            ydoc_id=ydoc_id,
        )
        assert access_group_ydoc is not None
        await access_group_ydoc.delete()

        ydoc = await YDoc.find_first_by_id(ydoc_id)
        assert ydoc is not None
        await ydoc.delete()


async def test_ydoc_creating_access_group_not_found(
    internal_client: TestClient,
    missing_access_group_id: UUID,
) -> None:
    assert_response(
        internal_client.post(
            f"/internal/storage-service/v2/access-groups/{missing_access_group_id}/ydocs/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Access group not found"},
    )
