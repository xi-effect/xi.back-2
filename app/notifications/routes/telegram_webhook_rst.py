from fastapi import HTTPException, Request
from starlette import status

from app.common.config import settings
from app.common.dependencies.telegram_auth_dep import (
    TelegramWebhookTokenHeader,
    WebhookTokenResponses,
)
from app.common.fastapi_ext import APIRouterExt
from app.notifications.config import telegram_app

router = APIRouterExt()


@router.post(
    path="/telegram-updates/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=WebhookTokenResponses.responses(),
    summary="Execute telegram webhook for notifications bot",
)
async def feed_updates_from_telegram(
    request: Request,
    webhook_token_header: TelegramWebhookTokenHeader = None,
) -> None:
    if settings.notifications_bot is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Notifications bot configuration is missing",
        )
    if (
        settings.notifications_bot.webhook_token is not None
        and webhook_token_header != settings.notifications_bot.webhook_token
    ):
        raise WebhookTokenResponses.INVALID_WEBHOOK_TOKEN
    await telegram_app.dispatcher.feed_webhook_update(
        bot=telegram_app.bot,
        update=await request.json(),
    )
