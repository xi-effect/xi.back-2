import random
from unittest.mock import call
from uuid import UUID

import pytest
from faker import Faker
from faststream.redis import RedisBroker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains

from app.common.config_bdg import notifications_bridge
from app.common.schemas.notifications_sch import (
    AnyNotificationPayloadSchema,
    NotificationInputSchema,
)
from app.common.utils.datetime import datetime_utc_now
from app.communities.rooms import user_room
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.routes.notifications_sub import send_notification
from app.notifications.services.senders.telegram_notification_sender import (
    TelegramNotificationSender,
)
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.common.tmexio_testing import TMEXIOListenerFactory
from tests.notifications import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_notification_send(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    faststream_broker: RedisBroker,
    tmexio_listener_factory: TMEXIOListenerFactory,
) -> None:
    recipient_user_ids = random.choices(list(range(1000)), k=faker.random_int(2, 5))

    notification_payload: AnyNotificationPayloadSchema = (
        factories.NotificationSimpleInputFactory.build().payload
    )
    input_data = NotificationInputSchema(
        payload=notification_payload,
        recipient_user_ids=recipient_user_ids * 2,
    )

    user_room_listeners = [
        await tmexio_listener_factory(room_name=user_room(recipient_user_id))
        for recipient_user_id in recipient_user_ids
    ]

    telegram_notification_sender_mock = mock_stack.enter_async_mock(
        TelegramNotificationSender, "send_notification"
    )

    send_notification.mock.reset_mock()

    await notifications_bridge.send_notification(data=input_data)

    notification_ids: set[UUID] = {
        user_room_listener.assert_next_event(
            expected_name="new-notification",
            expected_data={
                "id": UUID,
                "created_at": datetime_utc_now(),
                "payload": notification_payload.model_dump(mode="json"),
            },
        ).data["id"]
        for user_room_listener in user_room_listeners
    }
    assert len(notification_ids) == 1
    notification_id = notification_ids.pop()

    for user_room_listener in user_room_listeners:
        user_room_listener.assert_no_more_events()

    telegram_notification_sender_mock.assert_has_calls(
        [
            call(recipient_user_id=recipient_user_id)
            for recipient_user_id in recipient_user_ids
        ],
        any_order=True,
    )

    send_notification.mock.assert_called_once_with(input_data.model_dump(mode="json"))

    async with active_session():
        recipient_user_id_to_recipient_notification = {
            recipient_notification.recipient_user_id: recipient_notification
            for recipient_notification in await RecipientNotification.find_all_by_kwargs(
                notification_id=notification_id
            )
        }
        assert len(recipient_user_id_to_recipient_notification) == len(
            recipient_user_ids
        )

        for recipient_user_id in recipient_user_ids:
            assert_contains(
                recipient_user_id_to_recipient_notification.get(recipient_user_id),
                {"read_at": None},
            )

        notification = await Notification.find_first_by_id(notification_id)
        assert notification is not None
        await notification.delete()
