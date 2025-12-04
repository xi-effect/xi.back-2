from enum import StrEnum, auto
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class NotificationKind(StrEnum):
    INDIVIDUAL_INVITATION_ACCEPTED_V1 = auto()
    GROUP_INVITATION_ACCEPTED_V1 = auto()

    ENROLLMENT_CREATED_V1 = auto()

    CLASSROOM_CONFERENCE_STARTED_V1 = auto()

    RECIPIENT_INVOICE_CREATED_V1 = auto()
    STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1 = auto()


class InvitationAcceptanceNotificationPayloadSchema(BaseModel):
    kind: Literal[
        NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1,
        NotificationKind.GROUP_INVITATION_ACCEPTED_V1,
    ]

    invitation_id: int
    classroom_id: int
    student_id: int


class EnrollmentNotificationPayloadSchema(BaseModel):
    kind: Literal[NotificationKind.ENROLLMENT_CREATED_V1]

    classroom_id: int
    student_id: int


class ClassroomNotificationPayloadSchema(BaseModel):
    kind: Literal[NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1]

    classroom_id: int


class RecipientInvoiceNotificationPayloadSchema(BaseModel):
    kind: Literal[
        NotificationKind.RECIPIENT_INVOICE_CREATED_V1,
        NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1,
    ]

    recipient_invoice_id: int


AnyNotificationPayloadSchema = Annotated[
    InvitationAcceptanceNotificationPayloadSchema
    | EnrollmentNotificationPayloadSchema
    | ClassroomNotificationPayloadSchema
    | RecipientInvoiceNotificationPayloadSchema,
    Field(discriminator="kind"),
]


class NotificationInputSchema(BaseModel):
    payload: AnyNotificationPayloadSchema
    recipient_user_ids: Annotated[list[int], Field(min_length=1, max_length=100)]
