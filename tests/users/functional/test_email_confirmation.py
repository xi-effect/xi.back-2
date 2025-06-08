import time

import pytest
from faker import Faker
from starlette import status
from starlette.testclient import TestClient

from app.common.config import email_confirmation_cryptography
from app.users.models.users_db import User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.users.utils import get_db_user


@pytest.mark.anyio()
async def test_confirming_email(
    client: TestClient,
    active_session: ActiveSession,
    user: User,
) -> None:
    assert_nodata_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={"token": email_confirmation_cryptography.encrypt(user.email)},
        ),
    )

    async with active_session():
        assert (await get_db_user(user)).email_confirmed


@pytest.mark.anyio()
async def test_confirming_email_user_not_found(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={"token": email_confirmation_cryptography.encrypt(faker.email())},
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_email_invalid_token(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={"token": faker.text()},
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_email_expired_token(
    client: TestClient,
    user: User,
) -> None:
    expired_confirmation_token: bytes = (
        email_confirmation_cryptography.encryptor.encrypt_at_time(
            user.email.encode("utf-8"),
            current_time=int(time.time())
            - email_confirmation_cryptography.encryption_ttl
            - 1,
        )
    )

    assert_response(
        client.post(
            "/api/public/user-service/email-confirmation/confirmations/",
            json={"token": expired_confirmation_token.decode()},
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Invalid token"},
    )
