from datetime import timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from faker import Faker
from freezegun import freeze_time
from starlette import status
from starlette.testclient import TestClient

from app.common.schemas.pochta_sch import (
    EmailMessageInputSchema,
    EmailMessageKind,
    TokenEmailMessagePayloadSchema,
)
from app.common.utils.datetime import datetime_utc_now
from app.users.config import (
    PasswordResetTokenPayloadSchema,
    password_reset_token_provider,
)
from app.users.models.users_db import User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@pytest.fixture()
def new_password(faker: Faker) -> str:
    return faker.password()


async def test_requesting_password_reset(
    client: TestClient,
    send_email_message_mock: AsyncMock,
    user: User,
    new_password: str,
) -> None:
    assert_nodata_response(
        client.post(
            "/api/public/user-service/password-reset/requests/",
            json={"email": user.email},
        ),
        expected_code=status.HTTP_202_ACCEPTED,
    )

    expected_token = password_reset_token_provider.serialize_and_sign(
        PasswordResetTokenPayloadSchema(
            user_id=user.id,
            password_last_changed_at=user.password_last_changed_at,
        )
    )
    send_email_message_mock.assert_awaited_once_with(
        EmailMessageInputSchema(
            payload=TokenEmailMessagePayloadSchema(
                kind=EmailMessageKind.PASSWORD_RESET_V2,
                token=expected_token,
            ),
            recipient_emails=[user.email],
        )
    )


async def test_requesting_password_reset_user_not_found(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/password-reset/requests/",
            json={"email": faker.email()},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "User not found"},
    )


@freeze_time()
async def test_password_reset_confirmation(
    active_session: ActiveSession,
    client: TestClient,
    user: User,
    new_password: str,
) -> None:
    token = password_reset_token_provider.serialize_and_sign(
        PasswordResetTokenPayloadSchema(
            user_id=user.id,
            password_last_changed_at=user.password_last_changed_at,
        )
    )

    assert_nodata_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json={"token": token, "new_password": new_password},
        ),
    )

    async with active_session() as session:
        session.add(user)
        await session.refresh(user)

        assert user.is_password_valid(new_password)
        assert user.password_last_changed_at == datetime_utc_now()


async def test_password_reset_confirmation_with_old_password(
    active_session: ActiveSession,
    client: TestClient,
    user_data: AnyJSON,
    user: User,
) -> None:
    previous_password_last_changed_at = user.password_last_changed_at

    token = password_reset_token_provider.serialize_and_sign(
        PasswordResetTokenPayloadSchema(
            user_id=user.id,
            password_last_changed_at=user.password_last_changed_at,
        )
    )

    assert_nodata_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json={"token": token, "new_password": user_data["password"]},
        ),
    )

    async with active_session() as session:
        session.add(user)
        await session.refresh(user)

        assert user.password_last_changed_at == previous_password_last_changed_at


async def test_password_reset_confirmation_already_reset(
    faker: Faker,
    client: TestClient,
    user: User,
    new_password: str,
) -> None:
    token = password_reset_token_provider.serialize_and_sign(
        PasswordResetTokenPayloadSchema(
            user_id=user.id,
            password_last_changed_at=faker.date_time(
                tzinfo=timezone.utc,
                end_datetime=user.password_last_changed_at - timedelta(seconds=1),
            ),
        )
    )

    assert_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json={"token": token, "new_password": new_password},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )


async def test_password_reset_confirmation_user_not_found(
    client: TestClient,
    user: User,
    deleted_user_id: int,
    new_password: str,
) -> None:
    token = password_reset_token_provider.serialize_and_sign(
        PasswordResetTokenPayloadSchema(
            user_id=deleted_user_id,
            password_last_changed_at=user.password_last_changed_at,
        )
    )

    assert_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json={"token": token, "new_password": new_password},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )


async def test_password_reset_confirmation_expired_token(
    faker: Faker,
    client: TestClient,
    user: User,
    new_password: str,
) -> None:
    with freeze_time(
        faker.date_time(
            tzinfo=timezone.utc,
            end_datetime=datetime_utc_now() - timedelta(minutes=11),
        )
    ):
        token = password_reset_token_provider.serialize_and_sign(
            PasswordResetTokenPayloadSchema(
                user_id=user.id,
                password_last_changed_at=user.password_last_changed_at,
            )
        )

    assert_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json={"token": token, "new_password": new_password},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )


async def test_password_reset_confirmation_invalid_token(
    faker: Faker,
    client: TestClient,
    new_password: str,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json={"token": faker.word(), "new_password": new_password},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid token"},
    )
