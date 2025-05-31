from app.common.fastapi_ext import APIRouterExt
from app.users.dependencies.users_dep import UserByID, UserByUsername
from app.users.models.users_db import User

router = APIRouterExt(tags=["users"])


@router.get(
    "/users/by-id/{user_id}/profile/",
    response_model=User.UserProfileSchema,
    summary="Retrieve user profile by id",
)
async def get_profile_by_id(user: UserByID) -> User:
    return user


@router.get(
    "/users/by-username/{username}/profile/",
    response_model=User.UserProfileSchema,
    summary="Retrieve user profile by username",
)
async def get_profile_by_username(user: UserByUsername) -> User:
    return user
