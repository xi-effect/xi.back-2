from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, JsonValue
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.user_storage_items_dep import MyUserStorageItemByKey
from app.users.models.user_storage_items_db import UserStorageItem

router = APIRouterExt(tags=["user storage items"])


class UserStorageItemValueSchema(BaseModel):
    value: JsonValue


@router.get(
    path="/users/current/storage-items/{key}/",
    summary="Retrieve current user's storage item by key",
)
async def retrieve_user_storage_item(
    user_storage_item: MyUserStorageItemByKey,
) -> UserStorageItemValueSchema:
    return UserStorageItemValueSchema(value=user_storage_item.value)


class UserStorageItemValueResponses(Responses):
    USER_STORAGE_ITEM_VALUE_TOO_LARGE = (
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "User storage item value too large",
    )


@router.put(
    path="/users/current/storage-items/{key}/",
    responses=UserStorageItemValueResponses.responses(),
    summary="Set current user's storage item by key",
)
async def upsert_user_storage_item(
    auth_data: AuthorizationData,
    key: Annotated[UserStorageItem.KeyType, Path()],
    data: UserStorageItemValueSchema,
) -> UserStorageItemValueSchema:
    if UserStorageItem.is_value_too_large(data.value):
        raise UserStorageItemValueResponses.USER_STORAGE_ITEM_VALUE_TOO_LARGE
    await UserStorageItem.upsert(
        user_id=auth_data.user_id,
        key=key,
        value=data.value,
    )
    return data


@router.delete(
    path="/users/current/storage-items/{key}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user's storage item by key",
)
async def delete_user_storage_item(user_storage_item: MyUserStorageItemByKey) -> None:
    await user_storage_item.delete()
