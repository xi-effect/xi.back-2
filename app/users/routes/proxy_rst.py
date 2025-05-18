from contextlib import suppress
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi.security import APIKeyCookie, APIKeyHeader
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import (
    AUTH_COOKIE_NAME,
    AUTH_HEADER_NAME,
    add_session_to_response,
)

router = APIRouterExt(tags=["proxy auth"])

header_auth_scheme = APIKeyHeader(
    name=AUTH_HEADER_NAME, auto_error=False, scheme_name="auth header"
)
AuthHeader = Annotated[str | None, Depends(header_auth_scheme)]

cookie_auth_scheme = APIKeyCookie(
    name=AUTH_COOKIE_NAME, auto_error=False, scheme_name="auth cookie"
)
AuthCookie = Annotated[str | None, Depends(cookie_auth_scheme)]


class AuthorizedResponses(Responses):
    HEADER_MISSING = (HTTP_401_UNAUTHORIZED, "Authorization is missing")
    INVALID_SESSION = (HTTP_401_UNAUTHORIZED, "Session is invalid")


async def authorize_session(
    header_token: AuthHeader = None,
    cookie_token: AuthCookie = None,
) -> Session:
    token = cookie_token or header_token
    if token is None:
        raise AuthorizedResponses.HEADER_MISSING.value

    session = await Session.find_first_by_kwargs(token=token)
    if session is None or session.is_invalid:
        raise AuthorizedResponses.INVALID_SESSION.value

    return session


async def authorize_user(
    session: Session,
    response: Response,
) -> User:
    if session.is_renewal_required():
        session.renew()
        add_session_to_response(response, session)

    return await session.awaitable_attrs.user  # type: ignore[no-any-return]


@router.get(
    "/proxy/auth/",
    status_code=204,
    responses=AuthorizedResponses.responses(),
    summary="Retrieve headers for proxy authorization, return 401 on invalid auth",
)
async def proxy_auth(
    response: Response,
    x_request_method: Annotated[str | None, Header(alias="X-Request-Method")] = None,
    header_token: AuthHeader = None,
    cookie_token: AuthCookie = None,
) -> None:
    if x_request_method and x_request_method.upper() == "OPTIONS":
        return

    session = await authorize_session(
        header_token=header_token, cookie_token=cookie_token
    )
    user = await authorize_user(session, response)

    response.headers["X-Session-ID"] = str(session.id)
    response.headers["X-User-ID"] = str(user.id)
    response.headers["X-Username"] = user.username


@router.get(
    "/proxy/optional-auth/",
    status_code=204,
    summary="Retrieve headers for proxy authorization, do nothing on invalid auth",
)
async def optional_proxy_auth(
    response: Response,
    x_request_method: Annotated[str | None, Header(alias="X-Request-Method")] = None,
    header_token: AuthHeader = None,
    cookie_token: AuthCookie = None,
) -> None:
    with suppress(HTTPException):
        await proxy_auth(
            response=response,
            x_request_method=x_request_method,
            header_token=header_token,
            cookie_token=cookie_token,
        )
