from datetime import timezone
from typing import Final

from fastapi import Response

from app.common.config import settings
from app.users.models.sessions_db import Session

AUTH_HEADER_NAME: Final[str] = "X-XI-ID"
AUTH_COOKIE_NAME: Final[str] = "xi_id_token"


def add_session_to_response(response: Response, session: Session) -> None:
    response.set_cookie(
        AUTH_COOKIE_NAME,
        session.token,
        expires=session.expires_at.astimezone(timezone.utc),
        domain=settings.cookie_domain,
        samesite="none" if session.is_cross_site else "strict",
        httponly=True,
        secure=True,
    )


def remove_session_from_response(response: Response) -> None:
    response.delete_cookie(AUTH_COOKIE_NAME, domain=settings.cookie_domain)
