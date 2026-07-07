import logging
from unittest.mock import AsyncMock

import pytest

from app.common.schemas.pochta_sch import EmailMessageInputSchema
from app.notifications.models.delivery_methods_db import EmailDeliveryMethod
from app.notifications.models.notifications_db import Notification
from app.notifications.services.senders.email_notification_sender import (
    EmailNotificationSender,
)
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def email_notification_sender(
    notification: Notification,
) -> EmailNotificationSender:
    return EmailNotificationSender(notification=notification)


async def test_email_notification_sending(
    active_session: ActiveSession,
    authorized_user_id: int,
    send_email_message_mock: AsyncMock,
    active_email_delivery_method: EmailDeliveryMethod,
    email_notification_sender: EmailNotificationSender,
) -> None:
    async with active_session():
        await email_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    send_email_message_mock.assert_awaited_once_with(
        EmailMessageInputSchema(
            payload=email_notification_sender.email_message_payload,
            recipient_emails=[active_email_delivery_method.email],
        )
    )


async def test_email_notification_sending_email_delivery_method_not_found(
    active_session: ActiveSession,
    mock_stack: MockStack,
    authorized_user_id: int,
    send_email_message_mock: AsyncMock,
    notification: Notification,
    email_notification_sender: EmailNotificationSender,
) -> None:
    logging_error_mock = mock_stack.enter_mock(logging, "error")

    async with active_session():
        await email_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    logging_error_mock.assert_called_once_with(
        f"User {authorized_user_id} has no email delivery methods",
        extra={
            "notification_id": notification.id,
            "recipient_user_id": authorized_user_id,
        },
    )

    send_email_message_mock.assert_not_called()
