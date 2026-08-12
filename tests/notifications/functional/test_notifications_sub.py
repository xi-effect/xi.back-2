import random
from collections.abc import AsyncIterator
from datetime import UTC
from unittest.mock import call
from uuid import UUID

import pytest
from faker import Faker
from faststream.redis import RedisBroker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf

from app.common.config_bdg import notifications_bridge
from app.common.schemas.notifications_sch import NotificationInputV2Schema
from app.common.utils.datetime import datetime_utc_now
from app.communities.rooms import user_room
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.routes.notifications_sub import send_notification
from app.notifications.services import recipients_svc
from app.notifications.services.senders.email_notification_sender import (
    EmailNotificationSender,
)
from app.notifications.services.senders.platform_notification_sender import (
    PlatformNotificationSender,
)
from app.notifications.services.senders.telegram_notification_sender import (
    TelegramNotificationSender,
)
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.common.tmexio_testing import TMEXIOListenerFactory
from tests.notifications import factories

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def notification_data_no_idempotency() -> NotificationInputV2Schema:
    return factories.NotificationInputV2Factory.build(
        idempotency_key=None,
        idempotency_expires_at=None,
    )


@pytest.fixture()
async def notification_data_with_idempotency() -> NotificationInputV2Schema:
    return factories.NotificationInputV2WithIdempotencyFactory.build()


@pytest.fixture()
async def notification_with_expired_idempotency(
    faker: Faker,
    active_session: ActiveSession,
    notification_data_with_idempotency: NotificationInputV2Schema,
) -> AsyncIterator[Notification]:
    async with active_session():
        notification = await Notification.create(
            payload=notification_data_with_idempotency.payload,
            idempotency_key=notification_data_with_idempotency.idempotency_key,
            idempotency_expires_at=faker.past_datetime(tzinfo=UTC),
        )

    yield notification

    async with active_session():
        await notification.delete()


@pytest.mark.parametrize(
    ("notification_data", "existing_notification"),
    [
        pytest.param(
            lf("notification_data_no_idempotency"),
            None,
            id="no_idempotency_key",
        ),
        pytest.param(
            lf("notification_data_with_idempotency"),
            None,
            id="with_idempotency_key_no_stale_records",
        ),
        pytest.param(
            lf("notification_data_with_idempotency"),
            lf("notification_with_expired_idempotency"),
            id="with_idempotency_key_with_stale_records",
        ),
    ],
)
@freeze_time()
async def test_notification_send(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    faststream_broker: RedisBroker,
    tmexio_listener_factory: TMEXIOListenerFactory,
    notification_data: NotificationInputV2Schema,
    existing_notification: Notification | None,
) -> None:
    recipient_user_ids = random.sample(list(range(100)), k=faker.random_int(2, 5))

    generate_recipient_user_ids_for_notification_mock = mock_stack.enter_async_mock(
        recipients_svc,
        "generate_recipient_user_ids_for_notification",
        return_value=recipient_user_ids,
    )

    user_room_listeners = [
        await tmexio_listener_factory(room_name=user_room(recipient_user_id))
        for recipient_user_id in recipient_user_ids
    ]

    email_notification_sender_mock = mock_stack.enter_async_mock(
        EmailNotificationSender, "send_notification"
    )
    telegram_notification_sender_mock = mock_stack.enter_async_mock(
        TelegramNotificationSender, "send_notification"
    )

    send_notification.mock.reset_mock()

    await notifications_bridge.send_notification(data=notification_data)

    notification_ids: set[UUID] = {
        user_room_listener.assert_next_event(
            expected_name="new-notification",
            expected_data={
                "id": UUID,
                "created_at": datetime_utc_now(),
                "payload": notification_data.payload.model_dump(mode="json"),
            },
        ).data["id"]
        for user_room_listener in user_room_listeners
    }
    assert len(notification_ids) == 1
    notification_id = notification_ids.pop()

    for user_room_listener in user_room_listeners:
        user_room_listener.assert_no_more_events()

    generate_recipient_user_ids_for_notification_mock.assert_awaited_once_with(
        notification_data=notification_data,
    )

    sender_calls = [
        call(recipient_user_id=recipient_user_id)
        for recipient_user_id in recipient_user_ids
    ]
    email_notification_sender_mock.assert_has_calls(sender_calls, any_order=True)
    telegram_notification_sender_mock.assert_has_calls(sender_calls, any_order=True)

    send_notification.mock.assert_called_once_with(
        notification_data.model_dump(mode="json")
    )

    async with active_session() as session:
        if existing_notification is not None:
            session.add(existing_notification)
            await session.refresh(existing_notification)
            assert_contains(
                existing_notification,
                {
                    "idempotency_key": None,
                    "idempotency_expires_at": None,
                },
            )

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


@pytest.mark.parametrize(
    ("notification_data", "existing_notification"),
    [
        pytest.param(
            lf("notification_data_no_idempotency"),
            None,
            id="no_idempotency_key",
        ),
        pytest.param(
            lf("notification_data_with_idempotency"),
            None,
            id="with_idempotency_key_no_stale_records",
        ),
        pytest.param(
            lf("notification_data_with_idempotency"),
            lf("notification_with_expired_idempotency"),
            id="with_idempotency_key_with_stale_records",
        ),
    ],
)
@freeze_time()
async def test_notification_send_no_recipients_found(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    faststream_broker: RedisBroker,
    notification_data: NotificationInputV2Schema,
    existing_notification: Notification | None,
) -> None:
    generate_recipient_user_ids_for_notification_mock = mock_stack.enter_async_mock(
        recipients_svc,
        "generate_recipient_user_ids_for_notification",
        return_value=[],
    )

    platform_notification_sender_mock = mock_stack.enter_async_mock(
        PlatformNotificationSender, "send_notification"
    )
    email_notification_sender_mock = mock_stack.enter_async_mock(
        EmailNotificationSender, "send_notification"
    )
    telegram_notification_sender_mock = mock_stack.enter_async_mock(
        TelegramNotificationSender, "send_notification"
    )

    send_notification.mock.reset_mock()

    await notifications_bridge.send_notification(data=notification_data)

    send_notification.mock.assert_called_once_with(
        notification_data.model_dump(mode="json")
    )

    platform_notification_sender_mock.assert_not_called()
    email_notification_sender_mock.assert_not_called()
    telegram_notification_sender_mock.assert_not_called()

    generate_recipient_user_ids_for_notification_mock.assert_awaited_once_with(
        notification_data=notification_data,
    )

    async with active_session() as session:
        if existing_notification is not None:
            session.add(existing_notification)
            await session.refresh(existing_notification)
            assert_contains(
                existing_notification,
                {
                    "idempotency_key": None,
                    "idempotency_expires_at": None,
                },
            )

        assert_contains(
            list(await Notification.find_all_by_kwargs(created_at=datetime_utc_now())),
            [],
        )


@freeze_time()
async def test_notification_send_idempotency_violated(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    faststream_broker: RedisBroker,
) -> None:
    generate_recipient_user_ids_for_notification_mock = mock_stack.enter_async_mock(
        recipients_svc,
        "generate_recipient_user_ids_for_notification",
    )

    notification_data: NotificationInputV2Schema = (
        factories.NotificationInputV2WithIdempotencyFactory.build()
    )

    async with active_session():
        existing_notification = await Notification.create(
            payload=notification_data.payload,
            idempotency_key=notification_data.idempotency_key,
            idempotency_expires_at=notification_data.idempotency_expires_at,
        )

    platform_notification_sender_mock = mock_stack.enter_async_mock(
        PlatformNotificationSender, "send_notification"
    )
    email_notification_sender_mock = mock_stack.enter_async_mock(
        EmailNotificationSender, "send_notification"
    )
    telegram_notification_sender_mock = mock_stack.enter_async_mock(
        TelegramNotificationSender, "send_notification"
    )

    send_notification.mock.reset_mock()

    await notifications_bridge.send_notification(data=notification_data)

    send_notification.mock.assert_called_once_with(
        notification_data.model_dump(mode="json")
    )

    platform_notification_sender_mock.assert_not_called()
    email_notification_sender_mock.assert_not_called()
    telegram_notification_sender_mock.assert_not_called()

    generate_recipient_user_ids_for_notification_mock.assert_not_called()

    async with active_session():
        assert_contains(
            [
                notification.id
                for notification in await Notification.find_all_by_kwargs(
                    created_at=datetime_utc_now()
                )
            ],
            [existing_notification.id],
        )
