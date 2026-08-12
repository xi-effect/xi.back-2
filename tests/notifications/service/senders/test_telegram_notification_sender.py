import pytest
from aiogram.methods import SendMessage

from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.delivery_methods_db import TelegramDeliveryMethod
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)
from app.notifications.models.notifications_db import Notification
from app.notifications.services.senders.telegram_notification_sender import (
    TelegramNotificationSender,
)
from tests.common.active_session import ActiveSession
from tests.common.aiogram_testing import MockedBot
from tests.common.mock_stack import MockStack

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def telegram_notification_sender(
    notification: Notification,
) -> TelegramNotificationSender:
    return TelegramNotificationSender(notification=notification)


async def test_regular_telegram_notification_sending(
    active_session: ActiveSession,
    mock_stack: MockStack,
    mocked_bot: MockedBot,
    random_notification_category: NotificationCategory,
    active_telegram_delivery_method: TelegramDeliveryMethod,
    telegram_notification_sender: TelegramNotificationSender,
) -> None:
    mock_stack.enter_mock(
        TelegramNotificationSender,
        "notification_category",
        property_value=random_notification_category,
    )

    async with active_session():
        await telegram_notification_sender.send_notification(
            recipient_user_id=active_telegram_delivery_method.user_id
        )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": active_telegram_delivery_method.peer_id,
            "text": telegram_notification_sender.telegram_message_payload.message_text,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": telegram_notification_sender.telegram_message_payload.button_text,
                            "url": telegram_notification_sender.telegram_message_payload.button_link,
                        }
                    ]
                ]
            },
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_regular_telegram_notification_sending_inactive_delivery_route(
    active_session: ActiveSession,
    mock_stack: MockStack,
    mocked_bot: MockedBot,
    random_notification_category: NotificationCategory,
    active_telegram_delivery_method: TelegramDeliveryMethod,
    telegram_notification_sender: TelegramNotificationSender,
) -> None:
    mock_stack.enter_mock(
        TelegramNotificationSender,
        "notification_category",
        property_value=random_notification_category,
    )

    async with active_session():
        disabled_delivery_route = await DisabledDeliveryRoute.create(
            user_id=active_telegram_delivery_method.user_id,
            delivery_method_kind=DeliveryMethodKind.TELEGRAM,
            notification_category=random_notification_category,
        )

    async with active_session():
        await telegram_notification_sender.send_notification(
            recipient_user_id=active_telegram_delivery_method.user_id
        )

    mocked_bot.assert_no_more_api_calls()

    async with active_session():
        await disabled_delivery_route.delete()


async def test_system_telegram_notification_sending(
    active_session: ActiveSession,
    mock_stack: MockStack,
    mocked_bot: MockedBot,
    active_telegram_delivery_method: TelegramDeliveryMethod,
    telegram_notification_sender: TelegramNotificationSender,
) -> None:
    mock_stack.enter_mock(
        TelegramNotificationSender,
        "notification_category",
        property_value=None,
    )

    async with active_session():
        disabled_delivery_routes = [
            await DisabledDeliveryRoute.create(
                user_id=active_telegram_delivery_method.user_id,
                delivery_method_kind=DeliveryMethodKind.TELEGRAM,
                notification_category=notification_category,
            )
            for notification_category in NotificationCategory
        ]

    async with active_session():
        await telegram_notification_sender.send_notification(
            recipient_user_id=active_telegram_delivery_method.user_id
        )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": active_telegram_delivery_method.peer_id,
            "text": telegram_notification_sender.telegram_message_payload.message_text,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": telegram_notification_sender.telegram_message_payload.button_text,
                            "url": telegram_notification_sender.telegram_message_payload.button_link,
                        }
                    ]
                ]
            },
        },
    )
    mocked_bot.assert_no_more_api_calls()

    async with active_session():
        for disabled_delivery_route in disabled_delivery_routes:
            await disabled_delivery_route.delete()


@pytest.mark.usefixtures("inactive_telegram_delivery_method")
async def test_telegram_notification_sending_inactive_delivery_method(
    active_session: ActiveSession,
    authorized_user_id: int,
    mocked_bot: MockedBot,
    telegram_notification_sender: TelegramNotificationSender,
) -> None:
    async with active_session():
        await telegram_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    mocked_bot.assert_no_more_api_calls()


async def test_telegram_notification_sending_telegram_delivery_method_not_found(
    active_session: ActiveSession,
    authorized_user_id: int,
    mocked_bot: MockedBot,
    telegram_notification_sender: TelegramNotificationSender,
) -> None:
    async with active_session():
        await telegram_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    mocked_bot.assert_no_more_api_calls()
