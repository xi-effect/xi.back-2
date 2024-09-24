from typing import Annotated, Final

from fastapi import Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ValidationError
from starlette.status import HTTP_407_PROXY_AUTHENTICATION_REQUIRED

from app.common.fastapi_ext import Responses, with_responses

AUTH_SESSION_ID_HEADER_NAME: Final[str] = "X-Session-ID"
AUTH_USER_ID_HEADER_NAME: Final[str] = "X-User-ID"
AUTH_USERNAME_HEADER_NAME: Final[str] = "X-Username"

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

UsernameHeader = Annotated[
    str | None,
    Depends(
        APIKeyHeader(
            name=AUTH_USERNAME_HEADER_NAME,
            auto_error=False,
            scheme_name="username header",
        )
    ),
]


class ProxyAuthData(BaseModel):
    session_id: int
    user_id: int
    username: str

    @property
    def as_headers(self) -> dict[str, str]:
        return {
            AUTH_SESSION_ID_HEADER_NAME: str(self.session_id),
            AUTH_USER_ID_HEADER_NAME: str(self.user_id),
            AUTH_USERNAME_HEADER_NAME: self.username,
        }


def construct_proxy_auth_data(
    session_id_token: SessionIDHeader = None,
    user_id_token: UserIDHeader = None,
    username_token: UsernameHeader = None,
) -> ProxyAuthData:
    # may raise pydantic.ValidationError
    return ProxyAuthData(
        session_id=session_id_token,  # type: ignore[arg-type]
        user_id=user_id_token,  # type: ignore[arg-type]
        username=username_token,  # type: ignore[arg-type]
    )


class AuthorizedResponses(Responses):
    PROXY_AUTH_MISSING = HTTP_407_PROXY_AUTHENTICATION_REQUIRED, "Proxy auth required"


@with_responses(AuthorizedResponses)
async def authorize_proxy(
    session_id_token: SessionIDHeader = None,
    user_id_token: UserIDHeader = None,
    username_token: UsernameHeader = None,
) -> ProxyAuthData:
    try:  # using try-except to use pydantic's validation
        return construct_proxy_auth_data(
            session_id_token=session_id_token,
            user_id_token=user_id_token,
            username_token=username_token,
        )
    except ValidationError:  # noqa: WPS329  # bug  # TODO (36286438) pragma: no cover
        raise AuthorizedResponses.PROXY_AUTH_MISSING


ProxyAuthorized = Depends(authorize_proxy)
AuthorizationData = Annotated[ProxyAuthData, ProxyAuthorized]
