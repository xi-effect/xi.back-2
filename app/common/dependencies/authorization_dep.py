from typing import Annotated, Final

import sentry_sdk
from fastapi import Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ValidationError
from starlette import status

from app.common.fastapi_ext import Responses, with_responses

AUTH_SESSION_ID_HEADER_NAME: Final[str] = "X-Session-ID"
AUTH_USER_ID_HEADER_NAME: Final[str] = "X-User-ID"

SessionIDHeader = Annotated[
    str | None,
    Depends(
        APIKeyHeader(
            name=AUTH_SESSION_ID_HEADER_NAME,
            auto_error=False,
            scheme_name="session id header",
        )
    ),
]

UserIDHeader = Annotated[
    str | None,
    Depends(
        APIKeyHeader(
            name=AUTH_USER_ID_HEADER_NAME,
            auto_error=False,
            scheme_name="user id header",
        )
    ),
]


class ProxyAuthData(BaseModel):
    session_id: int
    user_id: int

    @property
    def as_headers(self) -> dict[str, str]:
        return {
            AUTH_SESSION_ID_HEADER_NAME: str(self.session_id),
            AUTH_USER_ID_HEADER_NAME: str(self.user_id),
        }


def construct_proxy_auth_data(
    session_id_token: SessionIDHeader = None,
    user_id_token: UserIDHeader = None,
) -> ProxyAuthData:
    return ProxyAuthData(
        session_id=session_id_token,
        user_id=user_id_token,
    )


class AuthorizedResponses(Responses):
    PROXY_AUTH_MISSING = status.HTTP_401_UNAUTHORIZED, "Proxy auth required"


@with_responses(AuthorizedResponses)
async def authorize_proxy(
    session_id_token: SessionIDHeader = None,
    user_id_token: UserIDHeader = None,
) -> ProxyAuthData:
    try:  # using try-except to use pydantic's validation
        proxy_auth_data = construct_proxy_auth_data(
            session_id_token=session_id_token,
            user_id_token=user_id_token,
        )
    except ValidationError:  # noqa: WPS329  # bug
        raise AuthorizedResponses.PROXY_AUTH_MISSING  # TODO (203) pragma: no cover

    sentry_sdk.set_user(
        {
            "id": proxy_auth_data.user_id,
            "session_id": proxy_auth_data.session_id,
        }
    )

    return proxy_auth_data


ProxyAuthorized = Depends(authorize_proxy)
AuthorizationData = Annotated[ProxyAuthData, ProxyAuthorized]
