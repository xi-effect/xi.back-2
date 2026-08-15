from unittest.mock import AsyncMock

import pytest

from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.common.schemas.pochta_sch import EmailMessageInputSchema
from app.notifications.models.delivery_methods_db import EmailDeliveryMethod
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)
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


async def test_regular_email_notification_sending(
    active_session: ActiveSession,
    mock_stack: MockStack,
    send_email_message_mock: AsyncMock,
    random_notification_category: NotificationCategory,
    active_email_delivery_method: EmailDeliveryMethod,
    email_notification_sender: EmailNotificationSender,
) -> None:
    mock_stack.enter_mock(
        EmailNotificationSender,
        "notification_category",
        property_value=random_notification_category,
    )

    async with active_session():
        await email_notification_sender.send_notification(
            recipient_user_id=active_email_delivery_method.user_id
        )

    send_email_message_mock.assert_awaited_once_with(
        EmailMessageInputSchema(
            payload=email_notification_sender.email_message_payload,
            recipient_emails=[active_email_delivery_method.email],
        )
    )


async def test_regular_email_notification_sending_inactive_delivery_route(
    active_session: ActiveSession,
    mock_stack: MockStack,
    send_email_message_mock: AsyncMock,
    random_notification_category: NotificationCategory,
    active_email_delivery_method: EmailDeliveryMethod,
    email_notification_sender: EmailNotificationSender,
) -> None:
    mock_stack.enter_mock(
        EmailNotificationSender,
        "notification_category",
        property_value=random_notification_category,
    )

    async with active_session():
        disabled_delivery_route = await DisabledDeliveryRoute.create(
            user_id=active_email_delivery_method.user_id,
            delivery_method_kind=DeliveryMethodKind.EMAIL,
            notification_category=random_notification_category,
        )

    async with active_session():
        await email_notification_sender.send_notification(
            recipient_user_id=active_email_delivery_method.user_id
        )

    send_email_message_mock.assert_not_called()

    async with active_session():
        await disabled_delivery_route.delete()


async def test_system_email_notification_sending(
    active_session: ActiveSession,
    mock_stack: MockStack,
    send_email_message_mock: AsyncMock,
    active_email_delivery_method: EmailDeliveryMethod,
    email_notification_sender: EmailNotificationSender,
) -> None:
    mock_stack.enter_mock(
        EmailNotificationSender,
        "notification_category",
        property_value=None,
    )

    async with active_session():
        disabled_delivery_routes = [
            await DisabledDeliveryRoute.create(
                user_id=active_email_delivery_method.user_id,
                delivery_method_kind=DeliveryMethodKind.EMAIL,
                notification_category=notification_category,
            )
            for notification_category in NotificationCategory
        ]

    async with active_session():
        await email_notification_sender.send_notification(
            recipient_user_id=active_email_delivery_method.user_id
        )

    send_email_message_mock.assert_awaited_once_with(
        EmailMessageInputSchema(
            payload=email_notification_sender.email_message_payload,
            recipient_emails=[active_email_delivery_method.email],
        )
    )

    async with active_session():
        for disabled_delivery_route in disabled_delivery_routes:
            await disabled_delivery_route.delete()


@pytest.mark.usefixtures("inactive_email_delivery_method")
async def test_email_notification_sending_email_inactive_delivery_method(
    active_session: ActiveSession,
    authorized_user_id: int,
    send_email_message_mock: AsyncMock,
    email_notification_sender: EmailNotificationSender,
) -> None:
    async with active_session():
        await email_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    send_email_message_mock.assert_not_called()


async def test_email_notification_sending_email_delivery_method_not_found(
    active_session: ActiveSession,
    authorized_user_id: int,
    send_email_message_mock: AsyncMock,
    email_notification_sender: EmailNotificationSender,
) -> None:
    async with active_session():
        await email_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    send_email_message_mock.assert_not_called()
