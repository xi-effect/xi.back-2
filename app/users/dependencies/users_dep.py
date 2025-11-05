from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.users.models.users_db import User


class CurrentUserResponses(Responses):
    USER_NOT_FOUND = status.HTTP_401_UNAUTHORIZED, "User not found"


@with_responses(CurrentUserResponses)
async def get_current_user(auth_data: AuthorizationData) -> User:
    user = await User.find_first_by_id(auth_data.user_id)
    if user is None:
        raise CurrentUserResponses.USER_NOT_FOUND
    return user


AuthorizedUser = Annotated[User, Depends(get_current_user)]


class TargetUserResponses(Responses):
    USER_NOT_FOUND = status.HTTP_404_NOT_FOUND, "User not found"


@with_responses(TargetUserResponses)
async def get_user_by_id(user_id: Annotated[int, Path()]) -> User:
    user = await User.find_first_by_id(user_id)
    if user is None:
        raise TargetUserResponses.USER_NOT_FOUND
    return user


UserByID = Annotated[User, Depends(get_user_by_id)]
