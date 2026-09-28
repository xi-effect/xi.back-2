from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.users.models.user_flag_kinds_db import UserFlagKind


class UserFlagKindResponses(Responses):
    USER_FLAG_KIND_NOT_FOUND = status.HTTP_404_NOT_FOUND, "User flag kind not found"


@with_responses(UserFlagKindResponses)
async def get_user_flag_kind_by_id(
    user_flag_kind_id: Annotated[int, Path()],
) -> UserFlagKind:
    user_flag_kind = await UserFlagKind.find_first_by_id(user_flag_kind_id)
    if user_flag_kind is None:
        raise UserFlagKindResponses.USER_FLAG_KIND_NOT_FOUND
    return user_flag_kind


UserFlagKindByID = Annotated[UserFlagKind, Depends(get_user_flag_kind_by_id)]
