from typing import Annotated

from fastapi import Depends
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.users.models.users_db import User


class CurrentUserResponses(Responses):
    USER_NOT_FOUND = HTTP_401_UNAUTHORIZED, "User not found"


@with_responses(CurrentUserResponses)
async def get_current_user(auth_data: AuthorizationData) -> User:
    user = await User.find_first_by_id(auth_data.user_id)
    if user is None:
        raise CurrentUserResponses.USER_NOT_FOUND
    return user


AuthorizedUser = Annotated[User, Depends(get_current_user)]
