from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains

from app.common.schemas.notifications_sch import NotificationKind
from app.notifications.models.notifications_db import Notification
from app.notifications.services import notifications_svc
from app.notifications.services.notification_adapters import (
    base_notification_adapter,
    classroom_notification_adapters,
    custom_notification_adapters,
    event_notification_adapters,
    recipient_invoice_notification_adapters,
)
from tests.common.active_session import ActiveSession
from tests.common.polyfactory_ext import BaseModelFactory
from tests.notifications.factories import NOTIFICATION_KIND_TO_PAYLOAD_FACTORY

pytestmark = pytest.mark.anyio

NOTIFICATION_KIND_TO_NOTIFICATION_ADAPTER_TYPE: dict[
    NotificationKind, type[base_notification_adapter.BaseNotificationAdapter[Any]]
] = {
    NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1: classroom_notification_adapters.IndividualInvitationAcceptedV1NotificationAdapter,
    NotificationKind.GROUP_INVITATION_ACCEPTED_V1: classroom_notification_adapters.GroupInvitationAcceptedV1NotificationAdapter,
    NotificationKind.ENROLLMENT_CREATED_V1: classroom_notification_adapters.EnrollmentCreatedV1NotificationAdapter,
    NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1: classroom_notification_adapters.ClassroomConferenceStartedV1NotificationAdapter,
    NotificationKind.RECIPIENT_INVOICE_CREATED_V1: recipient_invoice_notification_adapters.RecipientInvoiceCreatedV1NotificationAdapter,
    NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1: recipient_invoice_notification_adapters.StudentRecipientInvoicePaymentConfirmedV1NotificationAdapter,
    NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1: event_notification_adapters.SingleClassroomEventCreatedV1NotificationAdapter,
    NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1: event_notification_adapters.ClassroomEventInstanceRescheduledV1NotificationAdapter,
    NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1: event_notification_adapters.ClassroomEventInstanceCancelledV1NotificationAdapter,
    NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1: event_notification_adapters.PersistedClassroomEventInstanceReminderV1NotificationAdapter,
    NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1: event_notification_adapters.RepeatedClassroomEventInstanceReminderV1NotificationAdapter,
    NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1: event_notification_adapters.RepeatingClassroomEventCreatedV1NotificationAdapter,
    NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1: event_notification_adapters.ClassroomEventRepetitionUpdatedV1NotificationAdapter,
    NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1: event_notification_adapters.ClassroomEventRepetitionCancelledV1NotificationAdapter,
    NotificationKind.CUSTOM_V1: custom_notification_adapters.CustomV1NotificationAdapter,
}


@pytest.mark.parametrize(
    ("notification_kind", "payload_factory", "expected_notification_adapter_type"),
    [
        pytest.param(
            notification_kind,
            NOTIFICATION_KIND_TO_PAYLOAD_FACTORY[notification_kind],
            expected_notification_adapter_type,
            id=str(notification_kind),
        )
        for (
            notification_kind,
            expected_notification_adapter_type,
        ) in NOTIFICATION_KIND_TO_NOTIFICATION_ADAPTER_TYPE.items()
    ],
)
async def test_notification_adapter_building(
    active_session: ActiveSession,
    notification_kind: NotificationKind,
    payload_factory: type[BaseModelFactory[Any]],
    expected_notification_adapter_type: type[
        base_notification_adapter.BaseNotificationAdapter[Any]
    ],
) -> None:
    async with active_session():
        notification = await Notification.create(
            payload=payload_factory.build(kind=notification_kind),
        )

    notification_adapter = notifications_svc.build_notification_adapter(
        notification=notification,
    )

    assert_contains(
        {
            "adapter": notification_adapter,
            "notification": notification_adapter.notification,
            "payload": notification_adapter.payload,
        },
        {
            "adapter": expected_notification_adapter_type,
            "notification": notification,
            "payload": notification.payload,
        },
    )
