from typing import Annotated, Any, cast

from tmexio import AsyncSocket, register_dependency

from app.common.dependencies.authorization_dep import (
    AUTH_SESSION_ID_HEADER_NAME,
    AUTH_USER_ID_HEADER_NAME,
    AUTH_USERNAME_HEADER_NAME,
    ProxyAuthData,
)


def header_to_wsgi_var(header_name: str) -> str:
    return f"HTTP_{header_name.upper().replace('-', '_')}"


async def authorize_from_wsgi_environ(environ: dict[str, Any]) -> ProxyAuthData:
    return ProxyAuthData(
        session_id=environ.get(header_to_wsgi_var(AUTH_SESSION_ID_HEADER_NAME)),  # type: ignore[arg-type]
        user_id=environ.get(header_to_wsgi_var(AUTH_USER_ID_HEADER_NAME)),  # type: ignore[arg-type]
        username=environ.get(header_to_wsgi_var(AUTH_USERNAME_HEADER_NAME)),  # type: ignore[arg-type]
    )


@register_dependency()
async def retrieve_authorized_user(socket: AsyncSocket) -> ProxyAuthData:
    session = await socket.get_session()  # TODO better typing!!!
    return cast(ProxyAuthData, session["auth"])


AuthorizedUser = Annotated[ProxyAuthData, retrieve_authorized_user]