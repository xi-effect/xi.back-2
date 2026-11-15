from enum import StrEnum, auto
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class EmailMessageKind(StrEnum):
    EMAIL_CONFIRMATION_V2 = auto()
    EMAIL_CHANGE_V2 = auto()
    PASSWORD_RESET_V2 = auto()

    UNIVERSAL_V3 = auto()


class TokenEmailMessagePayloadSchema(BaseModel):
    kind: Literal[
        EmailMessageKind.EMAIL_CONFIRMATION_V2,
        EmailMessageKind.EMAIL_CHANGE_V2,
        EmailMessageKind.PASSWORD_RESET_V2,
    ]

    token: str


class UniversalEmailMessagePayloadSchema(BaseModel):
    kind: Literal[EmailMessageKind.UNIVERSAL_V3] = EmailMessageKind.UNIVERSAL_V3

    theme: str
    pre_header: str
    header: str
    content: str
    button_text: str
    button_link: str


AnyEmailMessagePayload = Annotated[
    TokenEmailMessagePayloadSchema | UniversalEmailMessagePayloadSchema,
    Field(discriminator="kind"),
]


class EmailMessageInputSchema(BaseModel):
    payload: AnyEmailMessagePayload
    recipient_emails: Annotated[list[str], Field(min_length=1, max_length=100)]
