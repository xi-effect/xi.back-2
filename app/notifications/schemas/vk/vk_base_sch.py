from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class MethodName(StrEnum):
    MESSAGES__SEND = "messages.send"
    USERS__GET = "users.get"


class ErrorSchema(BaseModel):
    # https://dev.vk.com/en/reference/errors
    model_config = ConfigDict(extra="allow")
    error_code: int


class ResponseWrapperSchema[ResponseSchema](BaseModel):
    response: ResponseSchema | None = None
    error: ErrorSchema | None = None
