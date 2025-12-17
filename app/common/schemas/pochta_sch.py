from enum import StrEnum, auto
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class EmailMessageKind(StrEnum):
    CUSTOM_V1 = auto()

    EMAIL_CONFIRMATION_V2 = auto()
    EMAIL_CHANGE_V2 = auto()
    PASSWORD_RESET_V2 = auto()

    INDIVIDUAL_INVITATION_ACCEPTED_V1 = auto()
    GROUP_INVITATION_ACCEPTED_V1 = auto()

    ENROLLMENT_CREATED_V1 = auto()

    CLASSROOM_CONFERENCE_STARTED_V1 = auto()

    RECIPIENT_INVOICE_CREATED_V1 = auto()
    STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1 = auto()


class CustomEmailMessagePayloadSchema(BaseModel):
    kind: Literal[EmailMessageKind.CUSTOM_V1]

    theme: str
    pre_header: str
    header: str
    content: str
    button_text: str
    button_link: str


class TokenEmailMessagePayloadSchema(BaseModel):
    kind: Literal[
        EmailMessageKind.EMAIL_CONFIRMATION_V2,
        EmailMessageKind.EMAIL_CHANGE_V2,
        EmailMessageKind.PASSWORD_RESET_V2,
    ]

    token: str


class BaseNotificationEmailMessagePayloadSchema(BaseModel):
    notification_id: UUID


class ClassroomNotificationEmailMessagePayloadSchema(
    BaseNotificationEmailMessagePayloadSchema
):
    kind: Literal[
        EmailMessageKind.INDIVIDUAL_INVITATION_ACCEPTED_V1,
        EmailMessageKind.GROUP_INVITATION_ACCEPTED_V1,
        EmailMessageKind.ENROLLMENT_CREATED_V1,
        EmailMessageKind.CLASSROOM_CONFERENCE_STARTED_V1,
    ]

    classroom_id: int


class RecipientInvoiceNotificationEmailMessagePayloadSchema(
    BaseNotificationEmailMessagePayloadSchema
):
    kind: Literal[
        EmailMessageKind.RECIPIENT_INVOICE_CREATED_V1,
        EmailMessageKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1,
    ]

    recipient_invoice_id: int


AnyEmailMessagePayload = Annotated[
    CustomEmailMessagePayloadSchema
    | TokenEmailMessagePayloadSchema
    | ClassroomNotificationEmailMessagePayloadSchema
    | RecipientInvoiceNotificationEmailMessagePayloadSchema,
    Field(discriminator="kind"),
]


class EmailMessageInputSchema(BaseModel):
    payload: AnyEmailMessagePayload
    recipient_emails: Annotated[list[str], Field(min_length=1, max_length=100)]
