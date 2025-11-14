from enum import StrEnum, auto
from typing import Annotated, Any, Literal

from annotated_types import MaxLen
from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt

# https://godocs.unisender.ru/web-api-ref?http#email-send
# Some unused options are skipped, some optional fields made into required ones


class UnisenderGoSubstitutionsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    __pydantic_extra__: dict[str, Any]


class UnisenderGoMetadataSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    __pydantic_extra__: dict[
        Annotated[str, MaxLen(64)],
        Annotated[str, MaxLen(1024)],
    ]

    campaign_id: NonNegativeInt | None = None


class UnisenderGoRecipientSchema(BaseModel):
    email: str = Field()
    substitutions: UnisenderGoSubstitutionsSchema = UnisenderGoSubstitutionsSchema()
    metadata: UnisenderGoMetadataSchema = UnisenderGoMetadataSchema()


class UnisenderGoMessageOptionsSchema(BaseModel):
    send_at: str | None = None
    unsubscribe_url: str | None = None


class UnisenderGoMessageSchema(BaseModel):
    recipients: Annotated[list[UnisenderGoRecipientSchema], MaxLen(500)]
    template_id: str
    tags: Annotated[list[Annotated[str, MaxLen(50)]], MaxLen(4)] = []
    global_substitutions: UnisenderGoSubstitutionsSchema = (
        UnisenderGoSubstitutionsSchema()
    )
    global_metadata: UnisenderGoMetadataSchema = UnisenderGoMetadataSchema()
    idempotence_key: Annotated[str, MaxLen(64)] | None = None
    headers: Annotated[dict[str, str], MaxLen(50)] = {}
    options: UnisenderGoMessageOptionsSchema = UnisenderGoMessageOptionsSchema()


class UnisenderGoSendEmailRequestSchema(BaseModel):
    message: UnisenderGoMessageSchema


class UnisenderGoFailedEmailStatusEnum(StrEnum):
    UNSUBSCRIBED = auto()
    INVALID = auto()
    DUPLICATE = auto()
    TEMPORARY_UNAVAILABLE = auto()
    PERMANENT_UNAVAILABLE = auto()
    COMPLAINED = auto()
    BLOCKED = auto()


class UnisenderGoSendEmailSuccessfulResponseSchema(BaseModel):
    status: Literal["success"]
    job_id: str
    emails: list[str] = []
    failed_emails: dict[str, UnisenderGoFailedEmailStatusEnum] = {}


class UnisenderGoSendEmailErrorResponseSchema(BaseModel):
    status: Literal["error"]
    message: str
    code: int
