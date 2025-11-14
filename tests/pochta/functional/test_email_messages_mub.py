import pytest
from starlette.testclient import TestClient

from app.common.bridges.pochta_bdg import PochtaBridge
from app.common.schemas.pochta_sch import EmailMessageInputSchema
from tests.common.assert_contains_ext import assert_nodata_response
from tests.common.mock_stack import MockStack
from tests.pochta import factories

pytestmark = pytest.mark.anyio


async def test_queueing_email_message_sending(
    mock_stack: MockStack,
    mub_client: TestClient,
    authorized_user_id: int,
) -> None:
    input_data: EmailMessageInputSchema = factories.EmailMessageInputFactory.build()

    send_email_message_mock = mock_stack.enter_async_mock(
        PochtaBridge, "send_email_message"
    )

    assert_nodata_response(
        mub_client.post(
            "/mub/pochta-service/email-messages/",
            json=input_data.model_dump(mode="json"),
        ),
    )

    send_email_message_mock.assert_awaited_once_with(input_data)
