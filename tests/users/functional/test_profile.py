from datetime import datetime, timedelta

import pytest
import rstr
from faker import Faker
from freezegun import freeze_time
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.users.models.users_db import User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON
from tests.users.utils import generate_username, get_db_user


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "pass_username", [False, True], ids=["no_username", "with_username"]
)
@pytest.mark.parametrize(
    "pass_display_name", [False, True], ids=["no_display_name", "with_display_name"]
)
@pytest.mark.parametrize("pass_theme", [False, True], ids=["no_theme", "with_theme"])
async def test_profile_updating(
    faker: Faker,
    authorized_client: TestClient,
    user_data: AnyJSON,
    user: User,
    pass_username: bool,
    pass_display_name: bool,
    pass_theme: bool,
) -> None:
    update_data: AnyJSON = {}
    if pass_username:
        update_data["username"] = generate_username()
    if pass_display_name:
        update_data["display_name"] = faker.name()
    if pass_theme:
        update_data["theme"] = "new_theme"

    assert_response(
        authorized_client.patch(
            "/api/protected/user-service/users/current/profile/", json=update_data
        ),
        expected_json={**user_data, **update_data, "id": user.id, "password": None},
    )


@pytest.mark.anyio()
async def test_profile_updating_conflict(
    authorized_client: TestClient,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.patch(
            "/api/protected/user-service/users/current/profile/",
            json={"username": other_user.username},
        ),
        expected_code=409,
        expected_json={"detail": "Username already in use"},
    )


@pytest.mark.anyio()
async def test_profile_updating_invalid_username(
    authorized_client: TestClient,
) -> None:
    invalid_username: str = rstr.xeger("^[^a-z0-9_.]{4,30}$")

    assert_response(
        authorized_client.patch(
            "/api/protected/user-service/users/current/profile/",
            json={"username": invalid_username},
        ),
        expected_code=422,
        expected_json={
            "detail": [
                {
                    "type": "string_pattern_mismatch",
                    "loc": ["body", "username"],
                }
            ],
        },
    )


@pytest.mark.anyio()
async def test_profile_updating_display_name_with_whitespaces(
    faker: Faker,
    authorized_client: TestClient,
    user_data: AnyJSON,
    user: User,
) -> None:
    new_display_name: str = rstr.xeger(r"^\s[a-zA-Z0-9]{2,30}\s$")

    assert_response(
        authorized_client.patch(
            "/api/protected/user-service/users/current/profile/",
            json={"display_name": new_display_name},
        ),
        expected_json={
            **user_data,
            "id": user.id,
            "display_name": new_display_name.strip(),
            "password": None,
        },
    )


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("display_name_length", "error_type"),
    [
        pytest.param(1, "string_too_short", id="too_short"),
        pytest.param(31, "string_too_long", id="too_long"),
    ],
)
async def test_profile_updating_invalid_display_name(
    faker: Faker,
    authorized_client: TestClient,
    display_name_length: int,
    error_type: str,
) -> None:
    invalid_display_name: str = "".join(faker.random_letters(display_name_length))

    assert_response(
        authorized_client.patch(
            "/api/protected/user-service/users/current/profile/",
            json={"display_name": invalid_display_name},
        ),
        expected_code=422,
        expected_json={
            "detail": [
                {
                    "type": error_type,
                    "loc": ["body", "display_name"],
                }
            ],
        },
    )


@pytest.mark.anyio()
async def test_resending_confirmation(
    active_session: ActiveSession,
    user: User,
    authorized_client: TestClient,
) -> None:
    with freeze_time():
        assert_nodata_response(
            authorized_client.post(
                "/api/protected/user-service/users/current/email-confirmation-requests/",
            )
        )

        # TODO: assert email sent
        async with active_session():
            assert (
                await get_db_user(user)
            ).allowed_confirmation_resend == datetime_utc_now() + timedelta(minutes=10)


@pytest.mark.anyio()
async def test_resending_confirmation_timeout_not_passed(
    active_session: ActiveSession,
    user: User,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        (await get_db_user(user)).set_confirmation_resend_timeout()

    assert_response(
        authorized_client.post(
            "/api/protected/user-service/users/current/email-confirmation-requests/",
        ),
        expected_code=429,
        expected_json={"detail": "Too many emails"},
    )


@pytest.mark.anyio()
async def test_changing_user_email(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    authorized_client: TestClient,
    user_data: AnyJSON,
    user: User,
) -> None:
    new_email = faker.email()

    with freeze_time():
        assert_response(
            authorized_client.put(
                "/api/protected/user-service/users/current/email/",
                json={"password": user_data["password"], "new_email": new_email},
            ),
            expected_json={**user_data, "email": new_email, "password": None},
        )

        # TODO: assert email sent
        async with active_session():
            updated_user = await get_db_user(user)
            assert updated_user.email == new_email
            assert (
                await get_db_user(user)
            ).allowed_confirmation_resend == datetime_utc_now() + timedelta(minutes=10)
            assert not updated_user.email_confirmed


@pytest.mark.anyio()
async def test_changing_user_email_too_many_emails(
    faker: Faker,
    active_session: ActiveSession,
    authorized_client: TestClient,
    user_data: AnyJSON,
    user: User,
) -> None:
    new_email = faker.email()

    async with active_session():
        (await get_db_user(user)).set_confirmation_resend_timeout()

    assert_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/email/",
            json={"password": user_data["password"], "new_email": new_email},
        ),
        expected_code=429,
        expected_json={"detail": "Too many emails"},
    )


@pytest.mark.anyio()
async def test_changing_user_email_conflict(
    authorized_client: TestClient,
    user_data: AnyJSON,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/email/",
            json={"password": user_data["password"], "new_email": other_user.email},
        ),
        expected_code=409,
        expected_json={"detail": "Email already in use"},
    )


@pytest.mark.anyio()
async def test_changing_user_email_wrong_password(
    faker: Faker,
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/email/",
            json={"password": faker.password(), "new_email": faker.email()},
        ),
        expected_code=401,
        expected_json={"detail": "Wrong password"},
    )


@pytest.mark.anyio()
async def test_changing_user_password(
    faker: Faker,
    active_session: ActiveSession,
    authorized_client: TestClient,
    user_data: AnyJSON,
    user: User,
) -> None:
    async with active_session():
        previous_last_password_change: datetime = (
            await get_db_user(user)
        ).last_password_change
    new_password: str = faker.password()

    assert_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/password/",
            json={"password": user_data["password"], "new_password": new_password},
        ),
        expected_json={**user_data, "password": None},
    )

    async with active_session():
        user_after_password_changing = await get_db_user(user)
        assert user_after_password_changing.is_password_valid(new_password)
        assert (
            user_after_password_changing.last_password_change
            > previous_last_password_change
        )


@pytest.mark.anyio()
async def test_changing_user_password_wrong_password(
    faker: Faker,
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/password/",
            json={"new_password": faker.password(), "password": faker.password()},
        ),
        expected_code=401,
        expected_json={"detail": "Wrong password"},
    )


@pytest.mark.anyio()
async def test_changing_user_password_old_password(
    authorized_client: TestClient,
    user_data: AnyJSON,
) -> None:
    assert_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/password/",
            json={
                "new_password": user_data["password"],
                "password": user_data["password"],
            },
        ),
        expected_code=409,
        expected_json={"detail": "New password matches the current one"},
    )
