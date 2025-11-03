from uuid import UUID

import pytest
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.storage_v2.models.access_groups_db import (
    AccessGroup,
    AccessGroupFile,
    AccessGroupYDoc,
)
from app.storage_v2.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response

pytestmark = pytest.mark.anyio


async def test_access_group_creation(
    active_session: ActiveSession,
    internal_client: TestClient,
) -> None:
    access_group_id: UUID = assert_response(
        internal_client.post("/internal/storage-service/v2/access-groups/"),
        expected_code=status.HTTP_201_CREATED,
        expected_json={"id": UUID},
    ).json()["id"]

    async with active_session():
        access_group = await AccessGroup.find_first_by_id(access_group_id)
        assert access_group is not None
        await access_group.delete()


async def test_access_group_duplication(
    active_session: ActiveSession,
    internal_client: TestClient,
    access_group: AccessGroup,
    ydoc: YDoc,
    access_group_ydoc: AccessGroupYDoc,
    access_group_file: AccessGroupFile,
) -> None:
    access_group_id: UUID = assert_response(
        internal_client.post(
            f"/internal/storage-service/v2/access-groups/{access_group.id}/duplicates/"
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={"id": UUID},
    ).json()["id"]

    async with active_session():
        access_group_ydocs = await AccessGroupYDoc.find_all_by_kwargs(
            access_group_id=access_group_id
        )
        assert len(access_group_ydocs) == 1

        assert_contains(
            await AccessGroupFile.find_all_by_kwargs(access_group_id=access_group_id),
            [{"file_id": access_group_file.file_id}],
        )

        new_access_group = await AccessGroup.find_first_by_id(access_group_id)
        assert new_access_group is not None
        await new_access_group.delete()

        new_ydoc = await YDoc.find_first_by_id(access_group_ydocs[0].ydoc_id)
        assert new_ydoc is not None
        assert_contains(new_ydoc, {"content": ydoc.content})
        await new_ydoc.delete()


async def test_access_group_duplication_no_ydocs(
    active_session: ActiveSession,
    internal_client: TestClient,
    access_group: AccessGroup,
    access_group_file: AccessGroupFile,
) -> None:
    access_group_id: UUID = assert_response(
        internal_client.post(
            f"/internal/storage-service/v2/access-groups/{access_group.id}/duplicates/"
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={"id": UUID},
    ).json()["id"]

    async with active_session():
        assert_contains(
            await AccessGroupYDoc.find_all_by_kwargs(access_group_id=access_group_id),
            [],
        )

        assert_contains(
            await AccessGroupFile.find_all_by_kwargs(access_group_id=access_group_id),
            [{"file_id": access_group_file.file_id}],
        )

        new_access_group = await AccessGroup.find_first_by_id(access_group_id)
        assert new_access_group is not None
        await new_access_group.delete()


async def test_access_group_deleting(
    active_session: ActiveSession,
    internal_client: TestClient,
    access_group: AccessGroup,
) -> None:
    assert_nodata_response(
        internal_client.delete(
            f"/internal/storage-service/v2/access-groups/{access_group.id}/"
        )
    )

    async with active_session():
        assert await AccessGroup.find_first_by_id(access_group.id) is None


async def test_access_group_deleting_access_group_not_found(
    internal_client: TestClient,
    missing_access_group_id: UUID,
) -> None:
    assert_response(
        internal_client.delete(
            f"/internal/storage-service/v2/access-groups/{missing_access_group_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Access group not found"},
    )
