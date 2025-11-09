import logging
from typing import Any

import pytest
from faker import Faker
from respx import MockRouter

from app.common.config_bdg import pochta_bridge
from app.common.schemas.pochta_sch import EmailMessageInputSchema, EmailMessageKind
from app.pochta.routes.email_messages_sub import (
    GLOBAL_TEMPLATE_VARIABLES,
    KIND_TO_TEMPLATE_ID,
    send_email_message,
)
from app.pochta.schemas.unisender_go_sch import (
    UnisenderGoMessageSchema,
    UnisenderGoRecipientSchema,
    UnisenderGoSendEmailRequestSchema,
    UnisenderGoSendEmailSuccessfulResponseSchema,
)
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.pochta import factories

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("kind", "payload_factory"),
    [
        pytest.param(
            EmailMessageKind.EMAIL_CONFIRMATION_V2,
            factories.TokenEmailMessagePayloadFactory,
            id="email_confirmation_v2",
        ),
        pytest.param(
            EmailMessageKind.EMAIL_CHANGE_V2,
            factories.TokenEmailMessagePayloadFactory,
            id="email_change_v2",
        ),
        pytest.param(
            EmailMessageKind.PASSWORD_RESET_V2,
            factories.TokenEmailMessagePayloadFactory,
            id="password_reset_v2",
        ),
        pytest.param(
            EmailMessageKind.INDIVIDUAL_INVITATION_ACCEPTED_V1,
            factories.ClassroomNotificationEmailMessagePayloadFactory,
            id="individual_invitation_accepted_v1",
        ),
        pytest.param(
            EmailMessageKind.GROUP_INVITATION_ACCEPTED_V1,
            factories.ClassroomNotificationEmailMessagePayloadFactory,
            id="group_invitation_accepted_v1",
        ),
        pytest.param(
            EmailMessageKind.ENROLLMENT_CREATED_V1,
            factories.ClassroomNotificationEmailMessagePayloadFactory,
            id="enrollment_created_v1",
        ),
        pytest.param(
            EmailMessageKind.CLASSROOM_CONFERENCE_STARTED_V1,
            factories.ClassroomNotificationEmailMessagePayloadFactory,
            id="classroom_conference_started_v1",
        ),
        pytest.param(
            EmailMessageKind.RECIPIENT_INVOICE_CREATED_V1,
            factories.RecipientInvoiceNotificationEmailMessagePayloadFactory,
            id="recipient_invoice_created_v1",
        ),
        pytest.param(
            EmailMessageKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1,
            factories.RecipientInvoiceNotificationEmailMessagePayloadFactory,
            id="student_recipient_invoice_payment_confirmed_v1",
        ),
    ],
)
async def test_email_message_sending(
    faker: Faker,
    unisender_go_api_key: str,
    unisender_go_mock: MockRouter,
    kind: EmailMessageKind,
    payload_factory: type[BaseModelFactory[Any]],
) -> None:
    input_data = EmailMessageInputSchema(
        payload=payload_factory.build(kind=kind),
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

    send_email_message.mock.assert_called_once_with(input_data.model_dump(mode="json"))

    assert_last_httpx_request(
        unisender_go_send_mock,
        expected_headers={"X-API-KEY": unisender_go_api_key},
        expected_json=UnisenderGoSendEmailRequestSchema(
            message=UnisenderGoMessageSchema(
                recipients=[
                    UnisenderGoRecipientSchema(email=recipient_email)
                    for recipient_email in input_data.recipient_emails
                ],
                template_id=KIND_TO_TEMPLATE_ID[kind],
                global_substitutions={
                    "global": GLOBAL_TEMPLATE_VARIABLES,
                    "data": input_data.payload.model_dump(mode="json"),
                },
            )
        ).model_dump(mode="json"),
    )


async def test_email_message_sending_unisender_failed(
    faker: Faker,
    mock_stack: MockStack,
    unisender_go_api_key: str,
    unisender_go_mock: MockRouter,
) -> None:
    failed_email: str = faker.email()

    input_data: EmailMessageInputSchema = factories.EmailMessageInputFactory.build(
        recipient_emails=[failed_email]
    )

    send_email_message.mock.reset_mock()

    logging_error_mock = mock_stack.enter_mock(logging, "error")

    unisender_go_response_data: UnisenderGoSendEmailSuccessfulResponseSchema = (
        factories.UnisenderGoSendEmailSuccessfulResponseFactory.build(emails=[])
    )

    unisender_go_send_mock = unisender_go_mock.post(
        path="/api/v1/email/send.json",
    ).respond(json=unisender_go_response_data.model_dump(mode="json"))

    await pochta_bridge.send_email_message(data=input_data)

    send_email_message.mock.assert_called_once_with(input_data.model_dump(mode="json"))

    logging_error_mock.assert_called_once_with(
        f"Sending email to {failed_email} failed",
        extra={
            "input_data": input_data,
            "unisender_go_response_data": unisender_go_response_data,
        },
    )

    assert_last_httpx_request(
        unisender_go_send_mock,
        expected_headers={"X-API-KEY": unisender_go_api_key},
        expected_json=UnisenderGoSendEmailRequestSchema(
            message=UnisenderGoMessageSchema(
                recipients=[
                    UnisenderGoRecipientSchema(email=recipient_email)
                    for recipient_email in input_data.recipient_emails
                ],
                template_id=KIND_TO_TEMPLATE_ID[input_data.payload.kind],
                global_substitutions={
                    "global": GLOBAL_TEMPLATE_VARIABLES,
                    "data": input_data.payload.model_dump(mode="json"),
                },
            )
        ).model_dump(mode="json"),
    )
