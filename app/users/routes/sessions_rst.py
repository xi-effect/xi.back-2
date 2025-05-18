from collections.abc import Sequence

from fastapi import Response
from starlette.status import HTTP_404_NOT_FOUND

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.sessions_dep import AuthorizedSession
from app.users.models.sessions_db import Session
from app.users.utils.authorization import remove_session_from_response

router = APIRouterExt(tags=["user sessions"])


@router.get(
    "/sessions/current/",
    response_model=Session.FullSchema,
    summary="Retrieve current session's data",
)
async def get_current_session(session: AuthorizedSession) -> Session:
    return session


@router.delete(
    "/sessions/current/",
    status_code=204,
    summary="Sign out from current account (disables the current session and removes cookies)",
)
async def signout(session: AuthorizedSession, response: Response) -> None:
    session.is_disabled = True
    remove_session_from_response(response)


@router.get(
    "/sessions/",
    response_model=list[Session.FullSchema],
    summary="List all current user's sessions but the current one",
)
async def list_sessions(auth_data: AuthorizationData) -> Sequence[Session]:
    return await Session.find_by_user(
        auth_data.user_id, exclude_id=auth_data.session_id
    )


@router.delete(
    "/sessions/",
    status_code=204,
    summary="Disable all current user's sessions but the current one",
)
async def disable_all_but_current(auth_data: AuthorizationData) -> None:
    await Session.disable_all_but_one_for_user(
        user_id=auth_data.user_id,
        excluded_id=auth_data.session_id,
    )


class SessionResponses(Responses):
    SESSION_NOT_FOUND = (HTTP_404_NOT_FOUND, Session.not_found_text)


@router.delete(
    "/sessions/{session_id}/",
    responses=SessionResponses.responses(),
    status_code=204,
    summary="Disable a specific user session",
)
async def disable_session(session_id: int, auth_data: AuthorizationData) -> None:
    session = await Session.find_first_by_kwargs(
        id=session_id,
        user_id=auth_data.user_id,
        is_mub=False,
    )
    if session is None:
        raise SessionResponses.SESSION_NOT_FOUND.value
    session.is_disabled = True
