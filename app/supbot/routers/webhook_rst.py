from fastapi import HTTPException, Request
from starlette import status

from app.common.config import settings
from app.common.dependencies.telegram_auth_dep import WebhookTokenResponses
from app.common.fastapi_ext import APIRouterExt
from app.supbot.config import telegram_app

router = APIRouterExt()


@router.post(
    path="/telegram-updates/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=WebhookTokenResponses.responses(),
    summary="Execute telegram webhook for supbot",
)
async def feed_updates_from_telegram(request: Request) -> None:
    if settings.supbot is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supbot configuration is missing",
        )
    await telegram_app.dispatcher.feed_webhook_update(
        bot=telegram_app.bot,
        update=await request.json(),
    )
