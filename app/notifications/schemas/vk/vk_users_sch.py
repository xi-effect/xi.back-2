from enum import StrEnum, auto

from pydantic import BaseModel, Field, TypeAdapter

from app.notifications.schemas.vk.vk_base_sch import ResponseWrapperSchema

# Reference for message-related schemas:
# https://github.com/VKCOM/vk-api-schema/tree/333481bd082ad747d4873ef4a77f9247097eeef0/users

# Some fields are intentionally omitted, because they are not used


class UserFieldName(StrEnum):
    SCREEN_NAME = auto()


class UsersGetInputSchema(BaseModel):
    # https://dev.vk.com/ru/method/users.get

    user_ids: list[int | str] = Field(max_length=1000)
    fields: list[UserFieldName]


class UserResponseSchema(BaseModel):
    # https://dev.vk.com/ru/reference/objects/user

    id: int
    first_name: str | None = None
    last_name: str | None = None
    screen_name: str | None = None


users_get_response_type_adapter = TypeAdapter(
    ResponseWrapperSchema[list[UserResponseSchema]]
)
