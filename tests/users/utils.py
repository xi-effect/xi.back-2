from http.cookiejar import Cookie

import pytest
import rstr
from httpx import Response
from pydantic_marshals.contains import TypeChecker, assert_contains

from app.common.config import settings
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME


def generate_username() -> str:
    return rstr.xeger("^[a-z0-9_.]{4,30}$")


async def get_db_user(user: User) -> User:
    db_user = await User.find_first_by_id(user.id)
    assert db_user is not None
    return db_user


async def get_db_session(session: Session) -> Session:
    db_session = await Session.find_first_by_id(session.id)
    assert db_session is not None
    return db_session


async def assert_session(token: str, invalid: bool = False) -> Session:
    session = await Session.find_first_by_kwargs(token=token)
    assert session is not None
    assert session.is_invalid == invalid
    return session


def find_auth_cookie(response: Response) -> Cookie:
    for cookie in response.cookies.jar:
        if cookie.name == AUTH_COOKIE_NAME:
            return cookie
    pytest.fail(f"{AUTH_COOKIE_NAME} not found in response")


async def assert_session_from_cookie(
    response: Response, is_cross_site: bool = False
) -> Session:
    cookie: Cookie = find_auth_cookie(response)

    assert_contains(
        {
            "value": cookie.value,
            "expired": cookie.is_expired(),
            "secure": cookie.secure,
            "domain": cookie.domain,
            "path": cookie.path,
            "httponly": cookie.has_nonstandard_attr("HttpOnly"),
            "same_site": cookie.get_nonstandard_attr("SameSite", "none"),
        },
        {
            "value": str,
            "expired": False,
            "secure": True,
            "domain": f".{settings.cookie_domain}",
            "path": "/",
            "httponly": True,
            "same_site": "none" if is_cross_site else "strict",
        },
    )
    assert cookie.value is not None  # for mypy
    assert isinstance(cookie.expires, int)  # for mypy

    session = await assert_session(cookie.value)
    assert_contains(
        {"is_cross_site": is_cross_site, "expires_at": cookie.expires},
        {
            "is_cross_site": session.is_cross_site,
            "expires_at": int(session.expires_at.timestamp()),
        },
    )
    return session


def session_checker(
    session: Session, check_mub: bool = False, is_invalid: bool = False
) -> TypeChecker:
    return {
        "id": session.id,
        "created_at": session.created_at,
        "expires_at": session.expires_at,
        "is_disabled": is_invalid,
        "is_invalid": is_invalid,
        "token": None,
        "is_mub": session.is_mub if check_mub else None,
    }
