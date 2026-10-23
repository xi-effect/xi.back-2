from pydantic import BaseModel

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.users.dependencies.user_flag_kinds_dep import UserFlagKindByKey
from app.users.models.user_flags_db import UserFlag

router = APIRouterExt(tags=["user flags"])


class UserFlagValueSchema(BaseModel):
    value: bool


@router.get(
    path="/users/current/flags/{key}/",
    summary="Retrieve current user's value for a user flag kind by key",
)
async def retrieve_user_flag(
    auth_data: AuthorizationData,
    user_flag_kind: UserFlagKindByKey,
) -> UserFlagValueSchema:
    user_flag = await UserFlag.find_first_by_primary_key(
        user_id=auth_data.user_id,
        user_flag_kind_id=user_flag_kind.id,
    )
    return UserFlagValueSchema(
        value=user_flag_kind.default_value if user_flag is None else user_flag.value,
    )


@router.put(
    path="/users/current/flags/{key}/",
    summary="Set current user's value for a user flag kind by key",
)
async def upsert_user_flag(
    auth_data: AuthorizationData,
    user_flag_kind: UserFlagKindByKey,
    data: UserFlagValueSchema,
) -> UserFlagValueSchema:
    await UserFlag.upsert(
        user_id=auth_data.user_id,
        user_flag_kind_id=user_flag_kind.id,
        value=data.value,
    )
    return data
