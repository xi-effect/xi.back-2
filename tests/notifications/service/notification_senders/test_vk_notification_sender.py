import pytest
from respx import MockRouter, Route

from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.delivery_methods_db import VKDeliveryMethod
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)
from app.notifications.models.notifications_db import Notification
from app.notifications.schemas.vk.vk_messages_sch import (
    KeyboardButtonSchema,
    KeyboardLinkButtonActionSchema,
    KeyboardSchema,
)
from app.notifications.services.notification_senders.vk_notification_sender import (
    VKNotificationSender,
)
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.common.respx_ext import assert_last_httpx_request

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def vk_notification_sender(
    notification: Notification,
) -> VKNotificationSender:
    return VKNotificationSender(notification=notification)


def assert_vk_notification_sent(
    vk_send_message_mock: Route,
    vk_notification_sender: VKNotificationSender,
    expected_peer_id: int,
) -> None:
    expected_keyboard = KeyboardSchema(
        inline=True,
        buttons=[
            [
                KeyboardButtonSchema(
                    action=KeyboardLinkButtonActionSchema(
                        link=vk_notification_sender.message_payload.button_link,
                        label=vk_notification_sender.message_payload.button_text,
                    )
                )
            ]
        ],
    )

    assert_last_httpx_request(
        vk_send_message_mock,
        expected_data={
            "peer_id": [str(expected_peer_id)],
            "message": [vk_notification_sender.message_payload.message_text],
            "keyboard": [expected_keyboard.model_dump_json()],
        },
    )


async def test_regular_vk_notification_sending(
    active_session: ActiveSession,
    mock_stack: MockStack,
    vk_send_message_mock: Route,
    random_notification_category: NotificationCategory,
    active_vk_delivery_method: VKDeliveryMethod,
    vk_notification_sender: VKNotificationSender,
) -> None:
    mock_stack.enter_mock(
        VKNotificationSender,
        "notification_category",
        property_value=random_notification_category,
    )

    async with active_session():
        await vk_notification_sender.send_notification(
            recipient_user_id=active_vk_delivery_method.user_id
        )

    assert_vk_notification_sent(
        vk_send_message_mock,
        vk_notification_sender,
        expected_peer_id=active_vk_delivery_method.peer_id,
    )


async def test_regular_vk_notification_sending_inactive_delivery_route(
    active_session: ActiveSession,
    mock_stack: MockStack,
    vk_respx_mock: MockRouter,
    random_notification_category: NotificationCategory,
    active_vk_delivery_method: VKDeliveryMethod,
    vk_notification_sender: VKNotificationSender,
) -> None:
    mock_stack.enter_mock(
        VKNotificationSender,
        "notification_category",
        property_value=random_notification_category,
    )

    async with active_session():
        disabled_delivery_route = await DisabledDeliveryRoute.create(
            user_id=active_vk_delivery_method.user_id,
            delivery_method_kind=DeliveryMethodKind.VK,
            notification_category=random_notification_category,
        )

    async with active_session():
        await vk_notification_sender.send_notification(
            recipient_user_id=active_vk_delivery_method.user_id
        )

    assert vk_respx_mock.calls.call_count == 0

    async with active_session():
        await disabled_delivery_route.delete()


async def test_system_vk_notification_sending(
    active_session: ActiveSession,
    mock_stack: MockStack,
    vk_send_message_mock: Route,
    active_vk_delivery_method: VKDeliveryMethod,
    vk_notification_sender: VKNotificationSender,
) -> None:
    mock_stack.enter_mock(
        VKNotificationSender,
        "notification_category",
        property_value=None,
    )

    async with active_session():
        disabled_delivery_routes = [
            await DisabledDeliveryRoute.create(
                user_id=active_vk_delivery_method.user_id,
                delivery_method_kind=DeliveryMethodKind.VK,
                notification_category=notification_category,
            )
            for notification_category in NotificationCategory
        ]

    async with active_session():
        await vk_notification_sender.send_notification(
            recipient_user_id=active_vk_delivery_method.user_id
        )

    assert_vk_notification_sent(
        vk_send_message_mock,
        vk_notification_sender,
        expected_peer_id=active_vk_delivery_method.peer_id,
    )

    async with active_session():
        for disabled_delivery_route in disabled_delivery_routes:
            await disabled_delivery_route.delete()


@pytest.mark.usefixtures("inactive_vk_delivery_method")
async def test_vk_notification_sending_inactive_delivery_method(
    active_session: ActiveSession,
    vk_respx_mock: MockRouter,
    authorized_user_id: int,
    vk_notification_sender: VKNotificationSender,
) -> None:
    async with active_session():
        await vk_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    assert vk_respx_mock.calls.call_count == 0


async def test_vk_notification_sending_vk_delivery_method_not_found(
    active_session: ActiveSession,
    vk_respx_mock: MockRouter,
    authorized_user_id: int,
    vk_notification_sender: VKNotificationSender,
) -> None:
    async with active_session():
        await vk_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    assert vk_respx_mock.calls.call_count == 0
