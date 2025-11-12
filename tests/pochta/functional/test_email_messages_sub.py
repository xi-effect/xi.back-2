import pytest
from respx import MockRouter

from app.common.config_bdg import pochta_bridge
from app.common.schemas.pochta_sch import EmailMessageInputSchema, EmailMessageKind
from app.pochta.routes.email_messages_sub import (
    BASE_FRONTEND_URL,
    KIND_TO_PATH,
    KIND_TO_TEMPLATE_ID,
    send_email_message,
)
from app.pochta.schemas.unisender_go_sch import (
    UnisenderGoMessageSchema,
    UnisenderGoRecipientSchema,
    UnisenderGoSendEmailRequestSchema,
)
from tests.common.respx_ext import assert_last_httpx_request
from tests.pochta import factories

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "email_message_kind",
    [pytest.param(kind, id=kind.value) for kind in EmailMessageKind],
)
async def test_email_message_send(
    unisender_go_api_key: str,
    unisender_go_mock: MockRouter,
    email_message_kind: EmailMessageKind,
) -> None:
    input_data: EmailMessageInputSchema = factories.EmailMessageInputFactory.build(
        kind=email_message_kind
    )

    send_email_message.mock.reset_mock()

    unisender_go_send_mock = unisender_go_mock.post(
        path="/api/v1/email/send.json",
    ).respond(json=factories.UnisenderGoSendEmailSuccessfulResponseFactory.build_json())

    await pochta_bridge.send_email_message(data=input_data)

    button_link = (
        BASE_FRONTEND_URL + KIND_TO_PATH[email_message_kind] + input_data.token
    )
    assert_last_httpx_request(
        unisender_go_send_mock,
        expected_headers={"X-API-KEY": unisender_go_api_key},
        expected_json=UnisenderGoSendEmailRequestSchema(
            message=UnisenderGoMessageSchema(
                recipients=[
                    UnisenderGoRecipientSchema(email=input_data.recipient_email)
                ],
                template_id=KIND_TO_TEMPLATE_ID[email_message_kind],
                global_substitutions={"button": {"link": button_link}},
            )
        ).model_dump(mode="json"),
    )

    send_email_message.mock.assert_called_once_with(input_data.model_dump(mode="json"))
