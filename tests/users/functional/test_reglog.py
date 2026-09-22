from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from faker import Faker
from freezegun import freeze_time
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.common.schemas.pochta_sch import (
    EmailMessageInputSchema,
    EmailMessageKind,
    TokenEmailMessagePayloadSchema,
)
from app.common.utils.datetime import datetime_utc_now
from app.users.config import (
    EmailConfirmationTokenPayloadSchema,
    email_confirmation_token_provider,
)
from app.users.models.users_db import OnboardingStage, User
from app.users.utils.authorization import AUTH_COOKIE_NAME
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON, PytestRequest
from tests.users.utils import assert_session_from_cookie

pytestmark = pytest.mark.anyio


@pytest.fixture(params=[False, True], ids=["same_site", "cross_site"])
def is_cross_site(request: PytestRequest[bool]) -> bool:
    return request.param


@freeze_time()
async def test_signing_up(
    notifications_respx_mock: MockRouter,
    active_session: ActiveSession,
    client: TestClient,
    send_email_message_mock: AsyncMock,
    user_data: AnyJSON,
    normalized_email: str,
    parametrized_email: str,
    is_cross_site: bool,
) -> None:
    notifications_bridge_mock = notifications_respx_mock.put(
        path__regex=rf"/users/(?P<user_id>\d+)/delivery-methods/{DeliveryMethodKind.EMAIL}/",
    ).respond(status_code=status.HTTP_201_CREATED)

    response = assert_response(
        client.post(
            "/api/public/user-service/signup/",
            json={**user_data, "email": parametrized_email},
            headers={"X-Testing": "true"} if is_cross_site else None,
        ),
        expected_json={
            **user_data,
            "email": normalized_email,
            "password": None,
            "id": int,
            "created_at": datetime_utc_now(),
            "display_name": user_data["username"],
            "default_layout": None,
            "theme": "system",
            "onboarding_stage": OnboardingStage.EMAIL_CONFIRMATION,
            "password_last_changed_at": datetime_utc_now(),
            "email_confirmation_resend_allowed_at": (
                datetime_utc_now() + timedelta(minutes=10)
            ),
        },
        expected_cookies={AUTH_COOKIE_NAME: str},
    )
    user_id = response.json()["id"]

    assert_last_httpx_request(
        notifications_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
        expected_path=f"/internal/notification-service/users/{user_id}/delivery-methods/email/",
        expected_json={"email": normalized_email},
    )

    expected_token = email_confirmation_token_provider.serialize_and_sign(
        EmailConfirmationTokenPayloadSchema(user_id=user_id)
    )
    send_email_message_mock.assert_awaited_once_with(
        EmailMessageInputSchema(
            payload=TokenEmailMessagePayloadSchema(
                kind=EmailMessageKind.EMAIL_CONFIRMATION_V2,
                token=expected_token,
            ),
            recipient_emails=[normalized_email],
        )
    )

    async with active_session():
        await assert_session_from_cookie(response, is_cross_site=is_cross_site)
        user = await User.find_first_by_id(response.json()["id"])
        assert user is not None
        assert user.is_password_valid(user_data["password"])
        await user.delete()


@pytest.mark.parametrize(
    ("data_mod", "error"),
    [
        pytest.param({"email": "n@new.new"}, "Username already in use", id="username"),
        pytest.param({"username": "new_one"}, "Email already in use", id="email"),
    ],
)
async def test_signing_up_conflict(
    client: TestClient,
    active_session: ActiveSession,
    user_data: AnyJSON,
    user: User,
    is_cross_site: bool,
    data_mod: AnyJSON,
    error: str,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/signup/",
            json={**user_data, **data_mod},
            headers={"X-Testing": "true"} if is_cross_site else None,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": error},
        expected_headers={"Set-Cookie": None},
    )


async def test_signing_in(
    client: TestClient,
    active_session: ActiveSession,
    user_data: AnyJSON,
    user_full_data: AnyJSON,
    is_cross_site: bool,
) -> None:
    response = assert_response(
        client.post(
            "/api/public/user-service/signin/",
            json=user_data,
            headers={"X-Testing": "true"} if is_cross_site else None,
        ),
        expected_json=user_full_data,
        expected_cookies={AUTH_COOKIE_NAME: str},
    )

    async with active_session():
        await assert_session_from_cookie(response, is_cross_site=is_cross_site)


@pytest.mark.usefixtures("user")
async def test_signing_in_user_not_found(
    faker: Faker,
    client: TestClient,
    user_data: AnyJSON,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/signin/",
            json={**user_data, "email": faker.email()},
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "User not found"},
        expected_headers={"Set-Cookie": None},
    )


@pytest.mark.usefixtures("user")
async def test_signing_in_wrong_password(
    faker: Faker,
    client: TestClient,
    user_data: AnyJSON,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/signin/",
            json={**user_data, "password": faker.password()},
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Wrong password"},
        expected_headers={"Set-Cookie": None},
    )


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("signup/", id="signup"),
        pytest.param("signin/", id="signin"),
    ],
)
async def test_reglog_invalid_email(
    faker: Faker,
    client: TestClient,
    user_data: AnyJSON,
    path: str,
) -> None:
    assert_response(
        client.post(
            f"/api/public/user-service/{path}",
            json={**user_data, "email": faker.word()},
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body", "email"],
                }
            ],
        },
        expected_headers={"Set-Cookie": None},
    )
