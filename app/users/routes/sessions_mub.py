from collections.abc import Sequence

from fastapi import Response
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.users_dep import UserByID
from app.users.models.sessions_db import Session
from app.users.utils.authorization import AUTH_COOKIE_NAME, add_session_to_response

router = APIRouterExt(tags=["sessions mub"])


def add_mub_session_to_response(response: Response, session: Session) -> None:
    add_session_to_response(response, session)

    response.headers["X-Session-ID"] = str(session.id)
    response.headers["X-User-ID"] = str(session.user_id)
    response.headers["X-Username"] = session.user.username

    response.headers["X-Session-Cookie"] = AUTH_COOKIE_NAME
    response.headers["X-Session-Token"] = session.token


@router.post(
    "/users/{user_id}/sessions/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new admin session",
)
async def make_mub_session(response: Response, user: UserByID) -> None:
    session = await Session.create(user_id=user.id, is_mub=True)
    add_mub_session_to_response(response, session)


@router.put(
    "/users/{user_id}/sessions/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retrieve or create an admin session",
)
async def upsert_mub_session(response: Response, user: UserByID) -> None:
    session = await Session.find_active_mub_session(user.id)
    if session is None:
        session = await Session.create(user_id=user.id, is_mub=True)
    add_mub_session_to_response(response, session)


@router.get(
    "/users/{user_id}/sessions/",
    response_model=list[Session.MUBFullSchema],
    summary="List all user sessions",
)
async def list_all_sessions(user: UserByID) -> Sequence[Session]:
    return await Session.find_all_by_kwargs(Session.expires_at.desc(), user_id=user.id)


class SessionResponses(Responses):
    SESSION_NOT_FOUND = status.HTTP_404_NOT_FOUND, Session.not_found_text


@router.delete(
    "/users/{user_id}/sessions/{session_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=SessionResponses.responses(),
    summary="Disable or delete any user session",
)
async def disable_or_delete_session(
    session_id: int,
    user: UserByID,
    delete_session: bool = False,
) -> None:
    session = await Session.find_first_by_kwargs(id=session_id, user_id=user.id)
    if session is None:
        raise SessionResponses.SESSION_NOT_FOUND
    if delete_session:
        await session.delete()
    else:
        session.is_disabled = True
