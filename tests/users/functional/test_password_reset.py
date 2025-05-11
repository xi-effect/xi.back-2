import time
from datetime import datetime

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.config import password_reset_cryptography
from app.users.models.users_db import User
from app.users.routes.password_reset_rst import ResetCredentials
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON
from tests.users import factories
from tests.users.utils import get_db_user


@pytest.mark.anyio()
async def test_requesting_password_reset(
    active_session: ActiveSession,
    mock_stack: MockStack,
    client: TestClient,
    user: User,
) -> None:
    assert_nodata_response(
        client.post(
            "/api/public/user-service/password-reset/requests/",
            json={"email": user.email},
        ),
        expected_code=202,
    )

    # TODO: assert email sent
    async with active_session():
        assert (await get_db_user(user)).reset_token is not None


@pytest.mark.anyio()
async def test_requesting_password_reset_user_not_found(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/password-reset/requests/",
            json={"email": faker.email()},
        ),
        expected_code=404,
        expected_json={"detail": "User not found"},
    )


@pytest.mark.anyio()
async def test_confirming_password_reset(
    active_session: ActiveSession,
    client: TestClient,
    user: User,
) -> None:
    async with active_session():
        db_user = await get_db_user(user)
        reset_token: str = db_user.generated_reset_token
        previous_last_password_change: datetime = db_user.last_password_change

    reset_data: ResetCredentials = factories.ResetCredentialsFactory.build(
        token=password_reset_cryptography.encrypt(reset_token)
    )

    assert_nodata_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json=reset_data.model_dump(mode="json"),
        ),
    )

    async with active_session():
        user_after_reset = await get_db_user(user)
        assert user_after_reset.is_password_valid(reset_data.new_password)
        assert user_after_reset.last_password_change > previous_last_password_change
        assert user_after_reset.reset_token is None


@pytest.mark.anyio()
async def test_confirming_password_reset_invalid_token(
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json=factories.ResetCredentialsFactory.build_json(),
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_password_reset_expired_token(
    active_session: ActiveSession,
    client: TestClient,
    user: User,
) -> None:
    async with active_session():
        reset_token: str = (await get_db_user(user)).generated_reset_token
    expired_reset_token: bytes = password_reset_cryptography.encryptor.encrypt_at_time(
        msg=reset_token.encode(),
        current_time=int(time.time()) - password_reset_cryptography.encryption_ttl - 1,
    )

    assert_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json=factories.ResetCredentialsFactory.build_json(
                token=expired_reset_token
            ),
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_password_reset_no_started_reset(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json=factories.ResetCredentialsFactory.build_json(
                token=password_reset_cryptography.encrypt(faker.text()),
            ),
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_password_reset_with_old_password(
    active_session: ActiveSession,
    client: TestClient,
    user_data: AnyJSON,
    user: User,
) -> None:
    async with active_session():
        db_user = await get_db_user(user)
        reset_token: str = db_user.generated_reset_token
        previous_last_password_change: datetime = db_user.last_password_change

    assert_nodata_response(
        client.post(
            "/api/public/user-service/password-reset/confirmations/",
            json={
                "token": password_reset_cryptography.encrypt(reset_token),
                "new_password": user_data["password"],
            },
        ),
    )

    async with active_session():
        assert (
            await get_db_user(user)
        ).last_password_change == previous_last_password_change
