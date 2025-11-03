from uuid import UUID

import pytest
from faststream.redis import RedisBroker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains

from app.common.config import settings
from app.common.utils.datetime import datetime_utc_now
from app.communities.rooms import user_room
from app.notifications.models.recipient_notifications_db import RecipientNotification
from tests.common.active_session import ActiveSession
from tests.common.tmexio_testing import TMEXIOListenerFactory
from tests.common.types import AnyJSON
from tests.notifications import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_notification_send_queueing(
    active_session: ActiveSession,
    faststream_broker: RedisBroker,
    authorized_user_id: int,
    tmexio_listener_factory: TMEXIOListenerFactory,
) -> None:
    input_data: AnyJSON = factories.NotificationSimpleInputFactory.build_json()

    user_room_listener = await tmexio_listener_factory(
        room_name=user_room(authorized_user_id)
    )

    await faststream_broker.publish(
        message={
            **input_data,
            "recipient_user_ids": [authorized_user_id],
        },
        stream=settings.notifications_send_stream_name,
    )

    notification_id: UUID = user_room_listener.assert_next_event(
        expected_name="new-notification",
        expected_data={
            "id": UUID,
            "created_at": datetime_utc_now(),
            **input_data,
        },
    ).data["id"]
    user_room_listener.assert_no_more_events()

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
