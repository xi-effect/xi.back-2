from typing import Annotated

from fastapi import Body
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.password_protected_dep import PasswordProtected
from app.users.dependencies.users_dep import AuthorizedUser
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.users import UsernameResponses, is_username_unique

router = APIRouterExt(tags=["current user"])


@router.get(
    path="/users/current/home/",
    response_model=User.FullSchema,
    summary="Retrieve current user's 'home' data",
)
async def get_user_data(user: AuthorizedUser) -> User:
    return user


@router.patch(
    path="/users/current/",
    response_model=User.FullSchema,
    responses=UsernameResponses.responses(),
    summary="Update current user's settings",
)
async def patch_user_data(data: User.SettingsPatchSchema, user: AuthorizedUser) -> User:
    if not await is_username_unique(data.username, user.username):
        raise UsernameResponses.USERNAME_IN_USE
    user.update(**data.model_dump(exclude_defaults=True))
    return user


class PasswordChangeResponses(Responses):
    PASSWORD_MATCHES_CURRENT = (
        status.HTTP_409_CONFLICT,
        "New password matches the current one",
    )


@router.put(
    path="/users/current/password/",
    response_model=User.FullSchema,
    responses=PasswordChangeResponses.responses(),
    summary="Update current user's password",
    dependencies=[PasswordProtected],
)
async def change_user_password(
    user: AuthorizedUser,
    auth_data: AuthorizationData,
    new_password: Annotated[str, Body(embed=True, min_length=6, max_length=100)],
) -> User:
    if user.is_password_valid(new_password):
        raise PasswordChangeResponses.PASSWORD_MATCHES_CURRENT

    user.change_password(new_password)

    await Session.disable_all_but_one_for_user(
        user_id=auth_data.user_id, excluded_id=auth_data.session_id
    )

    return user
