from pydantic_marshals.base import PatchDefault, PatchDefaultType
from starlette import status

from app.common.fastapi_ext import Responses
from app.users.models.users_db import User


class UsernameResponses(Responses):
    USERNAME_IN_USE = status.HTTP_409_CONFLICT, "Username already in use"


async def is_username_unique(
    patch_username: str | PatchDefaultType, current_username: str | None = None
) -> bool:
    if patch_username is not PatchDefault and patch_username != current_username:
        return await User.find_first_by_kwargs(username=patch_username) is None
    return True


class UserEmailResponses(Responses):
    EMAIL_IN_USE = status.HTTP_409_CONFLICT, "Email already in use"


async def is_email_unique(
    patch_email: str | PatchDefaultType, current_email: str | None = None
) -> bool:
    if patch_email is not PatchDefault and patch_email != current_email:
        return await User.find_first_by_kwargs(email=patch_email) is None
    return True
