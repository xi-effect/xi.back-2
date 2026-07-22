from typing import Literal

from pydantic import BaseModel, Field, NonNegativeInt, TypeAdapter

from app.notifications.schemas.vk.vk_base_sch import ResponseWrapperSchema

# Reference for message-related schemas:
# https://github.com/VKCOM/vk-api-schema/tree/333481bd082ad747d4873ef4a77f9247097eeef0/messages

# Some fields are intentionally omitted, because they are not used


class KeyboardLinkButtonActionSchema(BaseModel):
    type: Literal["open_link"]
    link: str
    label: str


class KeyboardButtonSchema(BaseModel):
    action: KeyboardLinkButtonActionSchema


class KeyboardSchema(BaseModel):
    # https://dev.vk.com/en/api/bots/development/keyboard

    one_time: bool = False
    inline: bool = False

    buttons: list[list[KeyboardButtonSchema]]


class MessageSendInputSchema(BaseModel):
    # https://dev.vk.com/en/method/messages.send

    peer_ids: list[int]

    random_id: int = 0
    message: str = Field(max_length=9000)

    keyboard: KeyboardSchema | None = None


class MessageSendPeerErrorSchema(BaseModel):
    code: int
    description: str


class MessageSendResponseItemSchema(BaseModel):
    # https://dev.vk.com/en/method/messages.send

    peer_id: int

    message_id: NonNegativeInt
    conversation_message_id: NonNegativeInt

    error: MessageSendPeerErrorSchema | None = None


send_message_response_type_adapter = TypeAdapter(
    ResponseWrapperSchema[list[MessageSendResponseItemSchema]]
)
