from datetime import timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from faker import Faker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.schemas.pochta_sch import (
    EmailMessageInputSchema,
    EmailMessageKind,
    TokenEmailMessagePayloadSchema,
)
from app.common.utils.datetime import datetime_utc_now
from app.users.config import EmailChangeTokenPayloadSchema, email_change_token_provider
from app.users.models.users_db import User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@pytest.fixture()
def new_email(faker: Faker) -> str:
    return faker.email()


@freeze_time()
async def test_requesting_email_change(
    faker: Faker,
    active_session: ActiveSession,
    send_email_message_mock: AsyncMock,
    authorized_client: TestClient,
    user_data: AnyJSON,
    user: User,
    new_email: str,
) -> None:
    async with active_session() as session:
        session.add(user)
        user.email_confirmation_resend_allowed_at = faker.past_datetime()

    assert_nodata_response(
        authorized_client.post(
            "/api/protected/user-service/users/current/email-change/requests/",
            json={"password": user_data["password"], "new_email": new_email},
        ),
        expected_code=status.HTTP_202_ACCEPTED,
    )

    expected_token = email_change_token_provider.serialize_and_sign(
        EmailChangeTokenPayloadSchema(
            user_id=user.id,
            new_email=new_email,
        )
    )
    send_email_message_mock.assert_awaited_once_with(
        EmailMessageInputSchema(
            payload=TokenEmailMessagePayloadSchema(
                kind=EmailMessageKind.EMAIL_CHANGE_V2,
                token=expected_token,
            ),
            recipient_emails=[new_email],
        )
    )

    async with active_session() as session:
        session.add(user)
        await session.refresh(user)

        assert_contains(
            user,
            {
                "email_confirmation_resend_allowed_at": datetime_utc_now()
                + timedelta(minutes=10),
            },
        )


async def test_requesting_email_change_too_many_emails(
    faker: Faker,
    active_session: ActiveSession,
    authorized_client: TestClient,
    user_data: AnyJSON,
    user: User,
    new_email: str,
) -> None:
    async with active_session() as session:
        session.add(user)
        await session.refresh(user)
        user.timeout_email_confirmation_resend()

    assert_response(
        authorized_client.post(
            "/api/protected/user-service/users/current/email-change/requests/",
            json={"password": user_data["password"], "new_email": new_email},
        ),
        expected_code=status.HTTP_429_TOO_MANY_REQUESTS,
        expected_json={"detail": "Too many emails"},
    )


async def test_requesting_email_change_email_already_in_use(
    authorized_client: TestClient,
    user_data: AnyJSON,
    other_user: User,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/user-service/users/current/email-change/requests/",
            json={"password": user_data["password"], "new_email": other_user.email},
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Email already in use"},
    )


async def test_requesting_email_change_wrong_password(
    faker: Faker,
    authorized_client: TestClient,
    new_email: str,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/user-service/users/current/email-change/requests/",
            json={"password": faker.password(), "new_email": new_email},
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Wrong password"},
    )


async def test_email_change_confirmation(
    notifications_respx_mock: MockRouter,
    client: TestClient,
    active_session: ActiveSession,
    user: User,
    new_email: str,
) -> None:
    notifications_bridge_mock = notifications_respx_mock.put(
        path=f"/users/{user.id}/email-connection/",
    ).respond(status_code=status.HTTP_204_NO_CONTENT)

    assert_nodata_response(
        client.post(
            "/api/public/user-service/email-change/confirmations/",
            json={
                "token": email_change_token_provider.serialize_and_sign(
                    EmailChangeTokenPayloadSchema(user_id=user.id, new_email=new_email)
                )
            },
        ),
    )

    assert_last_httpx_request(
        notifications_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
        expected_json={"email": new_email},
    )

    async with active_session() as session:
        session.add(user)
        await session.refresh(user)

        assert user.email == new_email


async def test_email_change_confirmation_email_already_in_use(
    client: TestClient,
    user: User,
    other_user: User,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/email-change/confirmations/",
            json={
                "token": email_change_token_provider.serialize_and_sign(
                    EmailChangeTokenPayloadSchema(
                        user_id=user.id,
                        new_email=other_user.email,
                    )
                )
            },
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Email already in use"},
    )


async def test_email_change_confirmation_user_not_found(
    client: TestClient,
    deleted_user_id: int,
    new_email: str,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/email-change/confirmations/",
            json={
                "token": email_change_token_provider.serialize_and_sign(
                    EmailChangeTokenPayloadSchema(
                        user_id=deleted_user_id,
                        new_email=new_email,
                    )
                )
            },
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )


async def test_email_change_confirmation_expired_token(
    faker: Faker,
    client: TestClient,
    user: User,
    new_email: str,
) -> None:
    with freeze_time(
        faker.date_time(
            tzinfo=timezone.utc,
            end_datetime=datetime_utc_now() - timedelta(minutes=11),
        )
    ):
        token = email_change_token_provider.serialize_and_sign(
            EmailChangeTokenPayloadSchema(user_id=user.id, new_email=new_email)
        )

    assert_response(
        client.post(
            "/api/public/user-service/email-change/confirmations/",
            json={"token": token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )


async def test_email_change_confirmation_invalid_token(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/email-change/confirmations/",
            json={"token": faker.text()},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )
