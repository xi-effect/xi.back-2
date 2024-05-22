import pytest
from starlette.testclient import TestClient

from app.communities.models.permissions_db import Permission, RolePermission
from app.communities.models.roles_db import Role
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import PytestRequest

pytestmark = pytest.mark.anyio

permission_list = [permission.value for permission in Permission]


@pytest.fixture(params=permission_list)
def permission(request: PytestRequest[str]) -> str:
    return request.param


async def test_permission_adding(
    mub_client: TestClient,
    active_session: ActiveSession,
    role: Role,
    permission: str,
) -> None:
    role_permission_id = assert_response(
        mub_client.post(
            f"/mub/community-service/roles/{role.id}/permissions/{permission}",
        ),
        expected_code=201,
        expected_json={
            "permission": permission,
        },
    ).json()["id"]

    async with active_session():
        role_permission = await RolePermission.find_first_by_id(role_permission_id)
        assert role_permission is not None
        await role_permission.delete()


async def test_permission_adding_already_added(
    mub_client: TestClient,
    active_session: ActiveSession,
    role: Role,
    permission: str,
) -> None:
    async with active_session():
        role_permission = await RolePermission.create(
            role_id=role.id, permission=permission
        )

    assert_response(
        mub_client.post(
            f"/mub/community-service/roles/{role.id}/permissions/{permission}",
        ),
        expected_code=409,
        expected_json={"detail": "Permission is already added"},
    )

    async with active_session():
        await role_permission.delete()


async def test_permission_removing(
    mub_client: TestClient,
    active_session: ActiveSession,
    role: Role,
    permission: str,
) -> None:
    async with active_session():
        role_permission_id = (
            await RolePermission.create(role_id=role.id, permission=permission)
        ).id

    assert_nodata_response(
        mub_client.delete(
            f"/mub/community-service/roles/{role.id}/permissions/{permission}",
        )
    )

    async with active_session():
        assert (await RolePermission.find_first_by_id(role_permission_id)) is None


async def test_permission_removing_misssin_permission(
    mub_client: TestClient,
    role: Role,
    permission: str,
) -> None:
    assert_response(
        mub_client.delete(
            f"/mub/community-service/roles/{role.id}/permissions/{permission}",
        ),
        expected_code=404,
        expected_json={"detail": "Role has no this permission"},
    )
