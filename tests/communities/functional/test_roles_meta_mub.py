from typing import Any

import pytest
from starlette.testclient import TestClient

from app.communities.models.communities_db import Community
from app.communities.models.roles_db import Permission, Role, RolePermission
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.communities.factories import RolePatchFactory

pytestmark = pytest.mark.anyio

permission_list = [permission.value for permission in Permission]


async def test_role_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
    role_data: AnyJSON,
) -> None:
    role_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/roles/",
            json=role_data,
        ),
        expected_code=201,
        expected_json={
            **role_data,
            "id": int,
        },
    ).json()["id"]

    async with active_session():
        role = await Role.find_first_by_id(role_id)
        assert role is not None
        await role.delete()


async def test_role_retrieving(
    mub_client: TestClient,
    active_session: ActiveSession,
    role: Role,
    role_data: AnyJSON,
) -> None:
    async with active_session():
        for permission in permission_list:
            await RolePermission.create(role_id=role.id, permission=permission)

    assert_response(
        mub_client.get(f"/mub/community-service/roles/{role.id}/"),
        expected_json={**role_data, "permissions": permission_list},
    )


async def test_role_updating(
    mub_client: TestClient,
    role: Role,
    role_data: AnyJSON,
) -> None:
    role_patch_data = RolePatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/community-service/roles/{role.id}/",
            json={"role_data": role_patch_data, "permissions": permission_list},
        ),
        expected_json={**role_data, **role_patch_data},
    )


async def test_role_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    role: Role,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/roles/{role.id}/")
    )

    async with active_session():
        assert (await Role.find_first_by_id(role.id)) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", RolePatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_role_not_finding(
    mub_client: TestClient,
    deleted_role_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/roles/{deleted_role_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=404,
        expected_json={"detail": "Role not found"},
    )
