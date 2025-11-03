import pytest

from app.common.config_bdg import notifications_bridge
from app.common.schemas.notifications_sch import NotificationInputSchema
from app.notifications.routes.notifications_sub import send_notification
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_notification_sending(
    authorized_user_id: int,
) -> None:
    input_data = NotificationInputSchema(
        payload=factories.NotificationSimpleInputFactory.build().payload,
        recipient_user_ids=[authorized_user_id],
    )

    send_notification.mock.reset_mock()

    await notifications_bridge.send_notification(data=input_data)

    send_notification.mock.assert_called_once_with(input_data.model_dump(mode="json"))
