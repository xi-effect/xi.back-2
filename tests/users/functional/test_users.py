import pytest
from starlette import status
from starlette.testclient import TestClient

from app.users.models.users_db import User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


async def test_getting_profile_by_id(
    authorized_client: TestClient,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.get(
            f"/api/protected/user-service/users/by-id/{other_user.id}/profile/"
        ),
        expected_json={
            "id": other_user.id,
            "username": other_user.username,
            "display_name": other_user.display_name,
        },
    )


async def test_getting_profile_by_id_not_found(
    authorized_client: TestClient,
    other_user: User,
    active_session: ActiveSession,
) -> None:
    async with active_session():
        await other_user.delete()
    assert_response(
        authorized_client.get(
            f"/api/protected/user-service/users/by-id/{other_user.id}/profile/"
        ),
        expected_json={"detail": "User not found"},
        expected_code=status.HTTP_404_NOT_FOUND,
    )


async def test_getting_profile_by_username(
    authorized_client: TestClient,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.get(
            f"/api/protected/user-service/users/by-username/{other_user.username}/profile/"
        ),
        expected_json={
            "id": other_user.id,
            "username": other_user.username,
            "display_name": other_user.display_name,
        },
    )


async def test_getting_profile_by_username_not_found(
    authorized_client: TestClient,
    other_user: User,
    active_session: ActiveSession,
) -> None:
    async with active_session():
        await other_user.delete()
    assert_response(
        authorized_client.get(
            f"/api/protected/user-service/users/by-username/{other_user.username}/profile/"
        ),
        expected_json={"detail": "User not found"},
        expected_code=status.HTTP_404_NOT_FOUND,
    )
