import pytest
from starlette import status
from starlette.testclient import TestClient

from app.common.bridges.pochta_bdg import PochtaBridge
from app.common.schemas.pochta_sch import EmailMessageInputSchema, EmailMessageKind
from app.users.config import (
    EmailConfirmationTokenPayloadSchema,
    email_confirmation_token_provider,
)
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON, PytestRequest
from tests.users.utils import assert_session_from_cookie

pytestmark = pytest.mark.anyio


@pytest.fixture(params=[False, True], ids=["same_site", "cross_site"])
def is_cross_site(request: PytestRequest[bool]) -> bool:
    return request.param


async def test_signing_up(
    active_session: ActiveSession,
    mock_stack: MockStack,
    client: TestClient,
    user_data: AnyJSON,
    is_cross_site: bool,
) -> None:
    send_email_message_mock = mock_stack.enter_async_mock(
        PochtaBridge, "send_email_message"
    )

    response = assert_response(
        client.post(
            "/api/public/user-service/signup/",
            json=user_data,
            headers={"X-Testing": "true"} if is_cross_site else None,
        ),
        expected_json={**user_data, "id": int, "password": None},
        expected_cookies={AUTH_COOKIE_NAME: str},
    )
    user_id = response.json()["id"]

    expected_token = email_confirmation_token_provider.serialize_and_sign(
        EmailConfirmationTokenPayloadSchema(user_id=user_id)
    )
    send_email_message_mock.assert_awaited_once_with(
        data=EmailMessageInputSchema(
            kind=EmailMessageKind.EMAIL_CONFIRMATION_V1,
            recipient_email=user_data["email"],
            token=expected_token,
        )
    )

    async with active_session():
        await assert_session_from_cookie(response, is_cross_site=is_cross_site)
        user = await User.find_first_by_id(response.json()["id"])
        assert user is not None
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
    user: User,
    is_cross_site: bool,
) -> None:
    response = assert_response(
        client.post(
            "/api/public/user-service/signin/",
            json=user_data,
            headers={"X-Testing": "true"} if is_cross_site else None,
        ),
        expected_json={**user_data, "id": user.id, "password": None},
        expected_cookies={AUTH_COOKIE_NAME: str},
    )

    async with active_session():
        await assert_session_from_cookie(response, is_cross_site=is_cross_site)


@pytest.mark.usefixtures("user")
@pytest.mark.parametrize(
    ("altered_key", "error"),
    [
        pytest.param("email", "User not found", id="bad_email"),
        pytest.param("password", "Wrong password", id="wrong_password"),
    ],
)
async def test_signing_in_invalid_credentials(
    client: TestClient,
    user_data: AnyJSON,
    altered_key: str,
    error: str,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/signin/", json={**user_data, altered_key: "alter"}
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": error},
        expected_headers={"Set-Cookie": None},
    )
