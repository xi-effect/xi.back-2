from unittest.mock import AsyncMock

import pytest
from starlette.testclient import TestClient

from app.common.schemas.pochta_sch import EmailMessageInputSchema
from tests.common.assert_contains_ext import assert_nodata_response
from tests.pochta import factories

pytestmark = pytest.mark.anyio


async def test_queueing_email_message_sending(
    mub_client: TestClient,
    authorized_user_id: int,
    send_email_message_mock: AsyncMock,
) -> None:
    input_data: EmailMessageInputSchema = factories.EmailMessageInputFactory.build()

    assert_nodata_response(
        mub_client.post(
            "/mub/pochta-service/email-messages/",
            json=input_data.model_dump(mode="json"),
        ),
    )

    send_email_message_mock.assert_awaited_once_with(input_data)
