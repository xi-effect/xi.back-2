import pytest
from starlette.testclient import TestClient

from app.common.bridges.notifications_bdg import NotificationsBridge
from app.common.schemas.notifications_sch import NotificationInputSchema
from tests.common.assert_contains_ext import assert_nodata_response
from tests.common.mock_stack import MockStack
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_queueing_notification_sending(
    mock_stack: MockStack,
    mub_client: TestClient,
    authorized_user_id: int,
) -> None:
    input_data = NotificationInputSchema(
        payload=factories.NotificationSimpleInputFactory.build().payload,
        recipient_user_ids=[authorized_user_id],
    )

    send_notification_mock = mock_stack.enter_async_mock(
        NotificationsBridge, "send_notification"
    )

    assert_nodata_response(
        mub_client.post(
            "/mub/notification-service/notifications/",
            json=input_data.model_dump(mode="json"),
        ),
    )

    send_notification_mock.assert_awaited_once_with(input_data)
