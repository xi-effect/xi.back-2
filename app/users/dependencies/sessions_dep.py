from typing import Annotated

from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.users.models.sessions_db import Session


class CurrentSessionResponses(Responses):
    SESSION_NOT_FOUND = status.HTTP_401_UNAUTHORIZED, "Session not found"


@with_responses(CurrentSessionResponses)
async def get_current_session(auth_data: AuthorizationData) -> Session:
    session = await Session.find_first_by_id(auth_data.session_id)
    if session is None:
        raise CurrentSessionResponses.SESSION_NOT_FOUND
    return session


AuthorizedSession = Annotated[Session, Depends(get_current_session)]
