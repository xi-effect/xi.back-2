import logging

from faststream.redis import RedisRouter

from app.common.config import settings
from app.common.faststream_ext import build_stream_sub
from app.common.schemas.pochta_sch import EmailMessageInputSchema, EmailMessageKind
from app.pochta.dependencies.unisender_go_dep import UnisenderGoClientDep
from app.pochta.schemas.unisender_go_sch import (
    UnisenderGoMessageSchema,
    UnisenderGoRecipientSchema,
    UnisenderGoSendEmailRequestSchema,
)

router = RedisRouter()

GLOBAL_TEMPLATE_VARIABLES: dict[str, str] = {
    "base_frontend_app_url": settings.frontend_app_base_url,
}

KIND_TO_TEMPLATE_ID: dict[EmailMessageKind, str] = {
    EmailMessageKind.EMAIL_CONFIRMATION_V2: "05b83984-bd89-11f0-81f1-122da0a24080",
    EmailMessageKind.EMAIL_CHANGE_V2: "a25aced8-bd88-11f0-b8e4-122da0a24080",
    EmailMessageKind.PASSWORD_RESET_V2: "3b5242e2-bd89-11f0-8132-025779db5bd3",
    EmailMessageKind.INDIVIDUAL_INVITATION_ACCEPTED_V1: "dfe2b0da-b7df-11f0-9a0e-1ecf01eb9d7d",
    EmailMessageKind.GROUP_INVITATION_ACCEPTED_V1: "5c4927c6-b7fe-11f0-8c0e-d2544595dc68",
    EmailMessageKind.ENROLLMENT_CREATED_V1: "8ae0674c-b7ff-11f0-a05c-d2544595dc68",
    EmailMessageKind.CLASSROOM_CONFERENCE_STARTED_V1: "0aef5510-b800-11f0-ad49-d2544595dc68",
    EmailMessageKind.RECIPIENT_INVOICE_CREATED_V1: "a466ca48-b800-11f0-80a2-d2544595dc68",
    EmailMessageKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1: "9c5cd7cc-b7fe-11f0-8d2e-d2544595dc68",
}


@router.subscriber(  # type: ignore[misc]  # bad typing in faststream
    stream=build_stream_sub(
        stream_name=settings.email_messages_send_stream_name,
        service_name="pochta-service",
    ),
)
async def send_email_message(
    unisender_go_client: UnisenderGoClientDep,
    data: EmailMessageInputSchema,
) -> None:
    message_data = UnisenderGoMessageSchema(
        recipients=[
            UnisenderGoRecipientSchema(email=recipient_email)
            for recipient_email in data.recipient_emails
        ],
        template_id=KIND_TO_TEMPLATE_ID[data.payload.kind],
        global_substitutions={
            "global": GLOBAL_TEMPLATE_VARIABLES,
            "data": data.payload.model_dump(mode="json"),
        },
    )

    unisender_go_response_data = await unisender_go_client.send_email(
        UnisenderGoSendEmailRequestSchema(message=message_data)
    )
    # TODO better error handling
    for recipient_email in data.recipient_emails:
        if recipient_email not in unisender_go_response_data.emails:
            logging.error(
                f"Sending email to {recipient_email} failed",
                extra={
                    "input_data": data,
                    "unisender_go_response_data": unisender_go_response_data,
                },
            )
