from uuid import UUID

import pytest
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
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.routes.notifications_sub import send_notification
from tests.common.active_session import ActiveSession
from tests.common.tmexio_testing import TMEXIOListenerFactory
from tests.notifications import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_notification_send(
    active_session: ActiveSession,
    faststream_broker: RedisBroker,
    authorized_user_id: int,
    tmexio_listener_factory: TMEXIOListenerFactory,
) -> None:
    notification_payload: AnyNotificationPayloadSchema = (
        factories.NotificationSimpleInputFactory.build().payload
    )
    input_data = NotificationInputSchema(
        payload=notification_payload,
        recipient_user_ids=[authorized_user_id],
    )

    user_room_listener = await tmexio_listener_factory(
        room_name=user_room(authorized_user_id)
    )

    send_notification.mock.reset_mock()

    await notifications_bridge.send_notification(data=input_data)

    notification_id: UUID = user_room_listener.assert_next_event(
        expected_name="new-notification",
        expected_data={
            "id": UUID,
            "created_at": datetime_utc_now(),
            "payload": notification_payload.model_dump(mode="json"),
        },
    ).data["id"]
    user_room_listener.assert_no_more_events()

    send_notification.mock.assert_called_once_with(input_data.model_dump(mode="json"))

    async with active_session():
        recipient_notifications = await RecipientNotification.find_all_by_kwargs(
            notification_id=notification_id
        )
        assert len(recipient_notifications) == 1
        assert_contains(
            recipient_notifications[0],
            {
                "recipient_user_id": authorized_user_id,
                "read_at": None,
            },
        )
