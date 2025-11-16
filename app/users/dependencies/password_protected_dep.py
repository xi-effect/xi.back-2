from typing import Annotated

from fastapi import Body, Depends
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.users.dependencies.users_dep import AuthorizedUser


class PasswordProtectedResponses(Responses):
    WRONG_PASSWORD = status.HTTP_401_UNAUTHORIZED, "Wrong password"


@with_responses(PasswordProtectedResponses)
async def validate_password(
    user: AuthorizedUser, password: Annotated[str, Body(embed=True)]
) -> None:
    if not user.is_password_valid(password):
        raise PasswordProtectedResponses.WRONG_PASSWORD


PasswordProtected = Depends(validate_password)
