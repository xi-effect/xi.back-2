import pytest
from faker import Faker
from respx import MockRouter

from app.common.config_bdg import pochta_bridge
from app.common.schemas.pochta_sch import (
    EmailMessageInputSchema,
    EmailMessageKind,
    TokenEmailMessagePayloadSchema,
)
from app.pochta.routes.email_messages_sub import (
    GLOBAL_TEMPLATE_VARIABLES,
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
async def test_email_message_sending_token_payload(
    faker: Faker,
    unisender_go_api_key: str,
    unisender_go_mock: MockRouter,
    email_message_kind: EmailMessageKind,
) -> None:
    input_data = EmailMessageInputSchema(
        payload=TokenEmailMessagePayloadSchema(
            kind=email_message_kind,
            token=faker.word(),
        ),
        recipient_emails=[faker.email() for _ in range(faker.random_int(2, 10))],
    )

    send_email_message.mock.reset_mock()

    unisender_go_send_mock = unisender_go_mock.post(
        path="/api/v1/email/send.json",
    ).respond(
        json=factories.UnisenderGoSendEmailSuccessfulResponseFactory.build_json(
            emails=input_data.recipient_emails
        )
    )

    await pochta_bridge.send_email_message(data=input_data)

    assert_last_httpx_request(
        unisender_go_send_mock,
        expected_headers={"X-API-KEY": unisender_go_api_key},
        expected_json=UnisenderGoSendEmailRequestSchema(
            message=UnisenderGoMessageSchema(
                recipients=[
                    UnisenderGoRecipientSchema(email=recipient_email)
                    for recipient_email in input_data.recipient_emails
                ],
                template_id=KIND_TO_TEMPLATE_ID[email_message_kind],
                global_substitutions={
                    "global": GLOBAL_TEMPLATE_VARIABLES,
                    "data": input_data.payload.model_dump(mode="json"),
                },
            )
        ).model_dump(mode="json"),
    )

    send_email_message.mock.assert_called_once_with(input_data.model_dump(mode="json"))
