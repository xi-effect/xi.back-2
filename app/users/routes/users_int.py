from typing import Annotated

from fastapi import Query

from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.users_sch import UserProfileSchema
from app.users.dependencies.users_dep import UserByID
from app.users.models.users_db import User

router = APIRouterExt(tags=["users internal"])


@router.get(
    path="/users/",
    response_model=dict[str, UserProfileSchema],
    summary="Retrieve multiple users by ids",
)
async def retrieve_multiple_users(
    user_ids: Annotated[list[int], Query(min_length=1, max_length=100)],
) -> dict[str, User]:
    return {
        str(user.id): user for user in await User.find_all_by_ids(user_ids=user_ids)
    }


@router.get(
    path="/users/{user_id}/",
    response_model=UserProfileSchema,
    summary="Retrieve user by ids",
)
async def retrieve_user(user: UserByID) -> User:
    return user
