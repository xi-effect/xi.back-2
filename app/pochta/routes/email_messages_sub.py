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

KIND_TO_TEMPLATE_ID: dict[EmailMessageKind, str] = {
    EmailMessageKind.EMAIL_CONFIRMATION_V1: "368ff086-85d7-11f0-8191-4619d70c5ec9",
    EmailMessageKind.EMAIL_CHANGE_V1: "166d9d92-b991-11f0-b704-1ecf01eb9d7d",
    EmailMessageKind.PASSWORD_RESET_V1: "659ee4dc-8365-11f0-bc22-3ea2c8a38738",
}

BASE_FRONTEND_URL: str = "https://app.sovlium.ru"

KIND_TO_PATH: dict[EmailMessageKind, str] = {
    EmailMessageKind.EMAIL_CONFIRMATION_V1: "/welcome/email/",
    EmailMessageKind.EMAIL_CHANGE_V1: "/confirm-email/",
    EmailMessageKind.PASSWORD_RESET_V1: "/reset-password/",
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
    button_link = BASE_FRONTEND_URL + KIND_TO_PATH[data.kind] + data.token
    message_data = UnisenderGoMessageSchema(
        recipients=[UnisenderGoRecipientSchema(email=data.recipient_email)],
        template_id=KIND_TO_TEMPLATE_ID[data.kind],
        global_substitutions={"button": {"link": button_link}},
    )

    response_data = await unisender_go_client.send_email(
        UnisenderGoSendEmailRequestSchema(message=message_data)
    )
    # TODO better error handling
    if data.recipient_email not in response_data.emails:
        logging.error("Sending email failed", extra={"full_error": response_data})
