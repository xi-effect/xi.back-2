from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, NonNegativeInt

# Reference for update schemas:
# https://github.com/VKCOM/vk-api-schema/blob/333481bd082ad747d4873ef4a77f9247097eeef0/callback/objects.json

# Some fields are intentionally omitted, because they are not used


class BaseUpdateSchema(BaseModel):
    group_id: NonNegativeInt
    event_id: str
    secret: str | None = None


class UpdateType(StrEnum):
    CONFIRMATION = "confirmation"
    ALLOW_MESSAGES = "message_allow"
    DENY_MESSAGES = "message_deny"


class ConfirmationUpdateSchema(BaseUpdateSchema):
    type: Literal[UpdateType.CONFIRMATION] = UpdateType.CONFIRMATION


class AllowMessagesObjectSchema(BaseModel):
    user_id: NonNegativeInt
    key: str = Field(max_length=255)


class AllowMessagesUpdateSchema(BaseUpdateSchema):
    type: Literal[UpdateType.ALLOW_MESSAGES] = UpdateType.ALLOW_MESSAGES
    object: AllowMessagesObjectSchema


class DenyMessagesObjectSchema(BaseModel):
    user_id: NonNegativeInt


class DenyMessagesUpdateSchema(BaseUpdateSchema):
    type: Literal[UpdateType.DENY_MESSAGES] = UpdateType.DENY_MESSAGES
    object: DenyMessagesObjectSchema


UpdateSchema = Annotated[
    ConfirmationUpdateSchema | AllowMessagesUpdateSchema | DenyMessagesUpdateSchema,
    Field(discriminator="type"),
]
