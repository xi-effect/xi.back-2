from unittest.mock import AsyncMock

import pytest
from starlette.testclient import TestClient

from app.common.schemas.notifications_sch import NotificationInputSchema
from tests.common.assert_contains_ext import assert_nodata_response
from tests.common.mock_stack import MockStack
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_queueing_notification_sending(
    mock_stack: MockStack,
    mub_client: TestClient,
    authorized_user_id: int,
    send_notification_mock: AsyncMock,
) -> None:
    input_data = NotificationInputSchema(
        payload=factories.NotificationSimpleInputFactory.build().payload,
        recipient_user_ids=[authorized_user_id],
    )

    assert_nodata_response(
        mub_client.post(
            "/mub/notification-service/notifications/",
            json=input_data.model_dump(mode="json"),
        ),
    )

    send_notification_mock.assert_awaited_once_with(input_data)
