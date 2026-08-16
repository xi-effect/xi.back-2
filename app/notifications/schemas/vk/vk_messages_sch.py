from typing import Literal

from pydantic import BaseModel, Field, TypeAdapter, field_serializer

from app.notifications.schemas.vk.vk_base_sch import ResponseWrapperSchema

# Reference for message-related schemas:
# https://github.com/VKCOM/vk-api-schema/tree/333481bd082ad747d4873ef4a77f9247097eeef0/messages

# Some fields are intentionally omitted, because they are not used


class KeyboardLinkButtonActionSchema(BaseModel):
    type: Literal["open_link"] = "open_link"
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

    peer_id: int

    random_id: int = 0
    message: str = Field(max_length=9000)

    keyboard: KeyboardSchema | None = None

    @field_serializer("keyboard")
    def serialize_keyboard(self, data: KeyboardSchema | None) -> str | None:
        if data is None:
            return None
        return data.model_dump_json()


send_message_response_type_adapter = TypeAdapter(ResponseWrapperSchema[int])
