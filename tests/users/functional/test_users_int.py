import pytest
from starlette import status
from starlette.testclient import TestClient

from app.users.models.users_db import User
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_retrieving_multiple_users(
    internal_client: TestClient,
    user: User,
    user_profile_data: AnyJSON,
    other_user: User,
    other_user_profile_data: AnyJSON,
) -> None:
    assert_response(
        internal_client.get(
            "/internal/user-service/users/",
            params={"user_ids": [user.id, other_user.id]},
        ),
        expected_json={
            str(user.id): user_profile_data,
            str(other_user.id): other_user_profile_data,
        },
    )


async def test_retrieving_multiple_users_user_not_found(
    internal_client: TestClient,
    deleted_user_id: int,
) -> None:
    assert_response(
        internal_client.get(
            "/internal/user-service/users/",
            params={"user_ids": [deleted_user_id]},
        ),
        expected_json={},
    )


async def test_user_retrieving(
    internal_client: TestClient,
    user: User,
    user_profile_data: AnyJSON,
) -> None:
    assert_response(
        internal_client.get(f"/internal/user-service/users/{user.id}/"),
        expected_json=user_profile_data,
    )


async def test_user_retrieving_user_not_found(
    internal_client: TestClient,
    deleted_user_id: int,
) -> None:
    assert_response(
        internal_client.get(f"/internal/user-service/users/{deleted_user_id}/"),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "User not found"},
    )
