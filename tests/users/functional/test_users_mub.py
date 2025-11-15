from typing import Any

import pytest
from faker import Faker
from freezegun import freeze_time
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.users.models.users_db import OnboardingStage, User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.users import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_user_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    user_data: AnyJSON,
) -> None:
    user_id: int = assert_response(
        mub_client.post("/mub/user-service/users/", json=user_data),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **user_data,
            "password": None,
            "id": int,
            "created_at": datetime_utc_now(),
            "display_name": user_data["username"],
            "default_layout": None,
            "theme": "system",
            "onboarding_stage": OnboardingStage.EMAIL_CONFIRMATION,
            "password_last_changed_at": datetime_utc_now(),
            "email_confirmation_resend_allowed_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        user = await User.find_first_by_id(user_id)
        assert user is not None
        assert user.is_password_valid(user_data["password"])
        await user.delete()


@pytest.mark.parametrize(
    ("pass_unique_email", "pass_unique_password", "error"),
    [
        pytest.param(True, False, "Username already in use", id="username"),
        pytest.param(False, True, "Email already in use", id="email"),
    ],
)
async def test_user_creation_conflict(
    faker: Faker,
    mub_client: TestClient,
    user_data: AnyJSON,
    user: User,
    pass_unique_email: bool,
    pass_unique_password: bool,
    error: str,
) -> None:
    data_modification: AnyJSON = {}
    if pass_unique_email:
        data_modification["email"] = faker.email()
    if pass_unique_password:
        data_modification["password"] = faker.password()

    assert_response(
        mub_client.post(
            "/mub/user-service/users/", json={**user_data, **data_modification}
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": error},
    )


async def test_user_getting(
    mub_client: TestClient,
    user: User,
    user_full_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/user-service/users/{user.id}/"),
        expected_json=user_full_data,
    )


async def test_user_updating(
    faker: Faker,
    mub_client: TestClient,
    user: User,
    user_full_data: AnyJSON,
) -> None:
    new_user_data: AnyJSON = factories.UserFullPatchFactory.build_json()

    assert_response(
        mub_client.patch(f"/mub/user-service/users/{user.id}/", json=new_user_data),
        expected_json={**user_full_data, **new_user_data, "password": None},
    )


@pytest.mark.parametrize(
    ("pass_used_email", "pass_used_username", "error"),
    [
        pytest.param(False, True, "Username already in use", id="username"),
        pytest.param(True, False, "Email already in use", id="email"),
    ],
)
async def test_user_updating_conflict(
    faker: Faker,
    mub_client: TestClient,
    other_user: User,
    user: User,
    pass_used_email: bool,
    pass_used_username: bool,
    error: str,
) -> None:
    data_modification: AnyJSON = {}
    if pass_used_email:
        data_modification["email"] = other_user.email
    if pass_used_username:
        data_modification["username"] = other_user.username

    assert_response(
        mub_client.patch(f"/mub/user-service/users/{user.id}/", json=data_modification),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": error},
    )


async def test_user_deleting(mub_client: TestClient, user: User) -> None:
    assert_nodata_response(mub_client.delete(f"/mub/user-service/users/{user.id}/"))


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
async def test_user_not_found(
    mub_client: TestClient,
    deleted_user_id: int,
    method: str,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/user-service/users/{deleted_user_id}/",
            json={} if method == "PATCH" else None,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "User not found"},
    )


async def test_user_updating_username_in_use(
    mub_client: TestClient,
    user: User,
    other_user: User,
) -> None:
    assert_response(
        mub_client.patch(
            f"/mub/user-service/users/{user.id}/",
            json={"username": other_user.username},
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Username already in use"},
    )


async def test_user_creation_invalid_mub_key(
    client: TestClient,
    user_data: AnyJSON,
    invalid_mub_key_headers: dict[str, Any] | None,
) -> None:
    assert_response(
        client.post(
            "/mub/user-service/users/",
            json=user_data,
            headers=invalid_mub_key_headers,
        ),
        expected_json={"detail": "Invalid key"},
        expected_code=status.HTTP_401_UNAUTHORIZED,
    )


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
async def test_user_operations_invalid_mub_key(
    client: TestClient,
    user: User,
    invalid_mub_key_headers: dict[str, Any] | None,
    method: str,
) -> None:
    assert_response(
        client.request(
            method,
            f"/mub/user-service/users/{user.id}/",
            json={},
            headers=invalid_mub_key_headers,
        ),
        expected_json={"detail": "Invalid key"},
        expected_code=status.HTTP_401_UNAUTHORIZED,
    )
