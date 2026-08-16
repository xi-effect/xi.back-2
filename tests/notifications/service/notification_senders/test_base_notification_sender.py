from typing import Any

import pytest

from app.common.schemas.notifications_sch import NotificationKind
from app.notifications.models.disabled_delivery_routes_db import NotificationCategory
from app.notifications.models.notifications_db import Notification
from app.notifications.services.notification_senders.base_notification_sender import (
    NOTIFICATION_KIND_TO_NOTIFICATION_CATEGORY,
    BaseNotificationSender,
)
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.notifications.factories import NOTIFICATION_KIND_TO_PAYLOAD_FACTORY

pytestmark = pytest.mark.anyio


class DummyNotificationSender(BaseNotificationSender):
    async def send_notification(self, recipient_user_id: int) -> None:
        pass


@pytest.mark.parametrize(
    ("notification_kind", "payload_factory", "expected_notification_category"),
    [
        pytest.param(
            notification_kind,
            NOTIFICATION_KIND_TO_PAYLOAD_FACTORY[notification_kind],
            expected_notification_category,
            id=str(notification_kind),
        )
        for (
            notification_kind,
            expected_notification_category,
        ) in NOTIFICATION_KIND_TO_NOTIFICATION_CATEGORY.items()
    ],
)
async def test_notification_category_converting(
    active_session: ActiveSession,
    mock_stack: MockStack,
    notification_kind: NotificationKind,
    payload_factory: type[BaseModelFactory[Any]],
    expected_notification_category: NotificationCategory | None,
) -> None:
    async with active_session():
        notification = await Notification.create(
            payload=payload_factory.build(kind=notification_kind)
        )

    notification_sender = DummyNotificationSender(notification=notification)

    assert notification_sender.notification_category == expected_notification_category
