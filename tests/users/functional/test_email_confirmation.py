import random
from datetime import timedelta, timezone

import pytest
from faker import Faker
from freezegun import freeze_time
from starlette import status
from starlette.testclient import TestClient

from app.common.bridges.pochta_bdg import PochtaBridge
from app.common.schemas.pochta_sch import EmailMessageInputSchema, EmailMessageKind
from app.common.utils.datetime import datetime_utc_now
from app.users.config import (
    EmailConfirmationTokenPayloadSchema,
    email_confirmation_token_provider,
)
from app.users.models.users_db import OnboardingStage, User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_requesting_confirmation_resend(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    user: User,
    authorized_client: TestClient,
) -> None:
    async with active_session() as session:
        session.add(user)
        user.email_confirmation_resend_allowed_at = faker.past_datetime()

    send_email_message_mock = mock_stack.enter_async_mock(
        PochtaBridge, "send_email_message"
    )

    assert_nodata_response(
        authorized_client.post(
            "/api/protected/user-service/users/current/email-confirmation/requests/",
        ),
        expected_code=status.HTTP_202_ACCEPTED,
    )

    expected_token: str = email_confirmation_token_provider.serialize_and_sign(
        EmailConfirmationTokenPayloadSchema(user_id=user.id)
    )
    send_email_message_mock.assert_awaited_once_with(
        data=EmailMessageInputSchema(
            kind=EmailMessageKind.EMAIL_CONFIRMATION_V1,
            recipient_email=user.email,
            token=expected_token,
        )
    )

    async with active_session() as session:
        session.add(user)
        await session.refresh(user)
        assert (
            user.email_confirmation_resend_allowed_at
            == datetime_utc_now() + timedelta(minutes=10)
        )


async def test_requesting_confirmation_resend_email_already_confirmed(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
) -> None:
    async with active_session() as session:
        session.add(user)
        user.onboarding_stage = random.choice(
            [
                onboarding_stage
                for onboarding_stage in OnboardingStage
                if onboarding_stage is not OnboardingStage.EMAIL_CONFIRMATION
            ]
        )

    assert_response(
        authorized_client.post(
            "/api/protected/user-service/users/current/email-confirmation/requests/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Email already confirmed"},
    )


async def test_requesting_confirmation_resend_too_many_emails(
    active_session: ActiveSession,
    user: User,
    authorized_client: TestClient,
) -> None:
    async with active_session() as session:
        session.add(user)
        user.timeout_email_confirmation_resend()

    assert_response(
        authorized_client.post(
            "/api/protected/user-service/users/current/email-confirmation/requests/",
        ),
        expected_code=status.HTTP_429_TOO_MANY_REQUESTS,
        expected_json={"detail": "Too many emails"},
    )


async def test_email_confirmation(
    client: TestClient,
    active_session: ActiveSession,
    user: User,
) -> None:
    assert_nodata_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={
                "token": email_confirmation_token_provider.serialize_and_sign(
                    EmailConfirmationTokenPayloadSchema(user_id=user.id)
                )
            },
        ),
    )

    async with active_session() as session:
        session.add(user)
        await session.refresh(user)

        assert user.onboarding_stage is OnboardingStage.USER_INFORMATION


async def test_email_confirmation_email_already_confirmed(
    faker: Faker,
    active_session: ActiveSession,
    client: TestClient,
    user: User,
) -> None:
    async with active_session() as session:
        session.add(user)
        user.onboarding_stage = random.choice(
            [
                onboarding_stage
                for onboarding_stage in OnboardingStage
                if onboarding_stage is not OnboardingStage.EMAIL_CONFIRMATION
            ]
        )

    assert_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={
                "token": email_confirmation_token_provider.serialize_and_sign(
                    EmailConfirmationTokenPayloadSchema(user_id=user.id)
                )
            },
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Email already confirmed"},
    )


async def test_email_confirmation_user_not_found(
    client: TestClient,
    deleted_user_id: int,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={
                "token": email_confirmation_token_provider.serialize_and_sign(
                    EmailConfirmationTokenPayloadSchema(user_id=deleted_user_id)
                )
            },
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )


async def test_email_confirmation_expired_token(
    faker: Faker,
    client: TestClient,
    user: User,
) -> None:
    with freeze_time(
        faker.date_time(
            tzinfo=timezone.utc,
            end_datetime=datetime_utc_now() - timedelta(minutes=11),
        )
    ):
        token = email_confirmation_token_provider.serialize_and_sign(
            EmailConfirmationTokenPayloadSchema(user_id=user.id)
        )

    assert_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={"token": token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )


async def test_email_confirmation_invalid_token(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={"token": faker.text()},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )
