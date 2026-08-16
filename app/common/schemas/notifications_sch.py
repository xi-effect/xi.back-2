from enum import StrEnum, auto
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from app.common.schemas.classrooms_sch import ClassroomRole


class NotificationKind(StrEnum):
    INDIVIDUAL_INVITATION_ACCEPTED_V1 = auto()
    GROUP_INVITATION_ACCEPTED_V1 = auto()

    ENROLLMENT_CREATED_V1 = auto()

    CLASSROOM_CONFERENCE_STARTED_V1 = auto()

    RECIPIENT_INVOICE_CREATED_V1 = auto()
    STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1 = auto()

    SINGLE_CLASSROOM_EVENT_CREATED_V1 = auto()
    CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1 = auto()  # TODO add `PERSISTED_` for V2
    CLASSROOM_EVENT_INSTANCE_CANCELLED_V1 = auto()

    REPEATING_CLASSROOM_EVENT_CREATED_V1 = auto()
    CLASSROOM_EVENT_REPETITION_UPDATED_V1 = auto()
    CLASSROOM_EVENT_REPETITION_CANCELLED_V1 = auto()

    PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1 = auto()
    REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1 = auto()

    CUSTOM_V1 = auto()


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


class PersistedClassroomEventInstanceNotificationPayloadSchema(BaseModel):
    kind: Literal[
        NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1,
        NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1,
        NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1,
        NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,
    ]

    classroom_id: int
    event_instance_id: UUID


class RepeatedClassroomEventInstanceNotificationPayloadSchema(BaseModel):
    kind: Literal[NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,]

    classroom_id: int
    repetition_mode_id: UUID
    instance_index: int


class ClassroomScheduleFocusNotificationPayloadSchema(BaseModel):
    kind: Literal[
        NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1,
        NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1,
        NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1,
    ]

    classroom_id: int
    focused_at: AwareDatetime


class CustomNotificationPayloadSchema(BaseModel):
    kind: Literal[NotificationKind.CUSTOM_V1]

    theme: str
    pre_header: str
    header: str
    content: str
    button_text: str
    button_link: str


AnyNotificationPayloadSchema = Annotated[
    InvitationAcceptanceNotificationPayloadSchema
    | EnrollmentNotificationPayloadSchema
    | ClassroomNotificationPayloadSchema
    | RecipientInvoiceNotificationPayloadSchema
    | PersistedClassroomEventInstanceNotificationPayloadSchema
    | RepeatedClassroomEventInstanceNotificationPayloadSchema
    | ClassroomScheduleFocusNotificationPayloadSchema
    | CustomNotificationPayloadSchema,
    Field(discriminator="kind"),
]


class RecipientKind(StrEnum):
    SINGLE_USER = auto()
    CLASSROOM_PARTICIPANT = auto()


class SingleUserRecipientFilterSchema(BaseModel):
    kind: Literal[RecipientKind.SINGLE_USER] = RecipientKind.SINGLE_USER

    user_id: int


class ClassroomParticipantRecipientFilterSchema(BaseModel):
    kind: Literal[RecipientKind.CLASSROOM_PARTICIPANT] = (
        RecipientKind.CLASSROOM_PARTICIPANT
    )

    classroom_id: int
    role: ClassroomRole | None


AnyRecipientFilterSchema = Annotated[
    SingleUserRecipientFilterSchema | ClassroomParticipantRecipientFilterSchema,
    Field(discriminator="kind"),
]


IdempotencyKeyType = Annotated[str | None, Field(min_length=1, max_length=100)]


class NotificationInputV2Schema(BaseModel):
    payload: AnyNotificationPayloadSchema
    recipient_filters: Annotated[
        list[AnyRecipientFilterSchema],
        Field(min_length=1, max_length=100),
    ]
    idempotency_key: IdempotencyKeyType = None
    idempotency_expires_at: AwareDatetime | None = None


# TODO (?) add recipient logic to payload instead?


class DeliveryMethodKind(StrEnum):
    EMAIL = auto()
    TELEGRAM = auto()
    VK = auto()
