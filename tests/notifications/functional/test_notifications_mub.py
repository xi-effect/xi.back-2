from uuid import UUID

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.communities.rooms import user_room
from app.notifications.models.recipient_notifications_db import (
    RecipientNotification,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.tmexio_testing import (
    TMEXIOListenerFactory,
)
from tests.common.types import AnyJSON
from tests.notifications import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_notification_sending(
    active_session: ActiveSession,
    mub_client: TestClient,
    authorized_user_id: int,
    tmexio_listener_factory: TMEXIOListenerFactory,
) -> None:
    input_data: AnyJSON = factories.NotificationSimpleInputFactory.build_json()

    user_room_listener = await tmexio_listener_factory(
        room_name=user_room(authorized_user_id)
    )

    notification_id = assert_response(
        mub_client.post(
            "/mub/notification-service/notifications/",
            json={
                **input_data,
                "recipient_user_ids": [authorized_user_id],
            },
        ),
        expected_json={
            "id": UUID,
            "created_at": datetime_utc_now(),
            **input_data,
        },
    ).json()["id"]

    user_room_listener.assert_next_event(
        expected_name="new-notification",
        expected_data={
            "id": notification_id,
            "created_at": datetime_utc_now(),
            **input_data,
        },
    )
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
