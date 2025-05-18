from datetime import timedelta
from typing import Any, Literal

import pytest
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.utils.datetime import datetime_utc_now
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME, AUTH_HEADER_NAME
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON, PytestRequest
from tests.users.utils import assert_session_from_cookie


@pytest.mark.anyio()
async def test_retrieving_home_data(
    authorized_client: TestClient,
    user_data: AnyJSON,
    user: User,
) -> None:
    assert_response(
        authorized_client.get("/api/protected/user-service/users/current/home/"),
        expected_json={**user_data, "id": user.id, "password": None},
    )


@pytest.fixture(params=[False, True], ids=["headers", "cookies"])
def use_cookie_auth(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.fixture()
async def authorized_proxy_client(
    client: TestClient,
    session: Session,
    use_cookie_auth: bool,
) -> TestClient:
    if use_cookie_auth:
        return TestClient(
            client.app,
            base_url=f"http://{settings.cookie_domain}",
            cookies={AUTH_COOKIE_NAME: session.token},
        )
    return TestClient(
        client.app,
        base_url=f"http://{settings.cookie_domain}",
        headers={AUTH_HEADER_NAME: session.token},
    )


@pytest.fixture(
    params=["/proxy/auth/", "/proxy/optional-auth/"],
    ids=["proxy_auth", "optional_proxy_auth"],
)
def proxy_auth_path(request: PytestRequest[str]) -> str:
    return request.param


@pytest.mark.anyio()
async def test_requesting_proxy_auth(
    authorized_proxy_client: TestClient,
    session: Session,
    user: User,
    proxy_auth_path: str,
) -> None:
    assert_nodata_response(
        authorized_proxy_client.get(proxy_auth_path),
        expected_headers={
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-ID": str(session.id),
        },
    )


@pytest.mark.anyio()
async def test_requesting_options_in_proxy_auth(
    authorized_proxy_client: TestClient,
    session: Session,
    user: User,
    proxy_auth_path: str,
) -> None:
    assert_nodata_response(
        authorized_proxy_client.get(
            proxy_auth_path,
            headers={"X-Request-Method": "OPTIONS"},
        ),
        expected_headers={
            "X-User-ID": None,
            "X-Username": None,
            "X-Session-ID": None,
        },
    )


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "invalid_token_in",
    [
        pytest.param(None, id="missing_header"),
        pytest.param("cookies", id="invalid_cookies"),
        pytest.param("headers", id="invalid_headers"),
    ],
)
async def test_optional_proxy_authorization_unauthorized(
    client: TestClient,
    invalid_token: str,
    invalid_token_in: Literal["cookies", "headers"] | None,
) -> None:
    kwargs: dict[str, Any] = (
        {invalid_token_in: {AUTH_COOKIE_NAME: invalid_token}}
        if invalid_token_in is not None
        else {}
    )
    assert_nodata_response(
        client.get("/proxy/optional-auth/", **kwargs),
        expected_cookies={AUTH_COOKIE_NAME: None},
        expected_headers={
            "X-User-ID": None,
            "X-Username": None,
            "X-Session-ID": None,
        },
    )


@pytest.mark.parametrize(
    "is_cross_site", [False, True], ids=["same_site", "cross_site"]
)
@pytest.mark.anyio()
async def test_renewing_session_in_proxy_auth(
    active_session: ActiveSession,
    authorized_proxy_client: TestClient,
    session: Session,
    user: User,
    proxy_auth_path: str,
    is_cross_site: bool,
) -> None:
    async with active_session() as db_session:
        session.expires_at = datetime_utc_now() + timedelta(hours=3)
        session.is_cross_site = is_cross_site
        db_session.add(session)

    response = assert_nodata_response(
        authorized_proxy_client.get(proxy_auth_path),
        expected_cookies={AUTH_COOKIE_NAME: str},
        expected_headers={
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-ID": str(session.id),
        },
    )

    async with active_session():
        session_from_cookie = await assert_session_from_cookie(response, is_cross_site)
        assert session_from_cookie.id == session.id


@pytest.mark.anyio()
async def test_requesting_unauthorized(client: TestClient) -> None:
    assert_response(
        client.get("/proxy/auth/"),
        expected_code=401,
        expected_json={"detail": "Authorization is missing"},
    )


@pytest.mark.anyio()
async def test_requesting_invalid_session(
    client: TestClient,
    invalid_token: str,
    use_cookie_auth: bool,
) -> None:
    cookies = {AUTH_COOKIE_NAME: invalid_token} if use_cookie_auth else {}
    headers = {} if use_cookie_auth else {AUTH_HEADER_NAME: invalid_token}
    assert_response(
        client.get("/proxy/auth/", cookies=cookies, headers=headers),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )
