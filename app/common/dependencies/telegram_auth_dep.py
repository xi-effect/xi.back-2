from typing import Annotated, Final

from fastapi import Depends
from fastapi.security import APIKeyHeader

TELEGRAM_WEBHOOK_TOKEN_HEADER_NAME: Final[str] = "X-Telegram-Bot-Api-Secret-Token"

telegram_webhook_token_scheme = APIKeyHeader(
    name=TELEGRAM_WEBHOOK_TOKEN_HEADER_NAME,
    auto_error=False,
    scheme_name="telegram webhook token header",
)
TelegramWebhookTokenHeader = Annotated[
    str | None, Depends(telegram_webhook_token_scheme)
]
