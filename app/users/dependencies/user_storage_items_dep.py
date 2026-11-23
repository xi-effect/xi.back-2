from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.users.models.user_storage_items_db import UserStorageItem


class UserStorageItemResponses(Responses):
    USER_STORAGE_ITEM_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "User storage item not found",
    )


@with_responses(UserStorageItemResponses)
async def get_my_user_storage_item_by_key(
    auth_data: AuthorizationData,
    key: Annotated[UserStorageItem.KeyType, Path()],
) -> UserStorageItem:
    user_storage_item = await UserStorageItem.find_first_by_primary_key(
        user_id=auth_data.user_id,
        key=key,
    )
    if user_storage_item is None:
        raise UserStorageItemResponses.USER_STORAGE_ITEM_NOT_FOUND
    return user_storage_item


MyUserStorageItemByKey = Annotated[
    UserStorageItem,
    Depends(get_my_user_storage_item_by_key),
]
