from unittest.mock import Mock

import pytest
from pydantic_marshals.contains import assert_contains

from app.common.schemas import notifications_sch
from app.notifications.services.notification_adapters.custom_notification_adapters import (
    CustomV1NotificationAdapter,
)
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_custom_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.CustomNotificationPayloadSchema = (
        factories.CustomNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.CUSTOM_V1,
        )
    )

    notification_adapter = CustomV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_contains(
        notification_adapter.to_messenger_message_payload(),
        {
            "message_text": f"{notification_payload.header}\n\n{notification_payload.content}",
            "button_text": notification_payload.button_text,
            "button_link": notification_payload.button_link,
        },
    )


async def test_custom_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.CustomNotificationPayloadSchema = (
        factories.CustomNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.CUSTOM_V1,
        )
    )

    notification_adapter = CustomV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_contains(
        notification_adapter.to_universal_email_message_payload(),
        {
            "theme": notification_payload.theme,
            "pre_header": notification_payload.pre_header,
            "header": notification_payload.header,
            "content": notification_payload.content,
            "button_text": notification_payload.button_text,
            "button_link": notification_payload.button_link,
        },
    )
