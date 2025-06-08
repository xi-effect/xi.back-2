from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Request
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.supbot.routers import (
    error_handling_tgm,
    start_tgm,
    support_team_tgm,
    support_tgm,
    vacancy_tgm,
)
from app.supbot.setup import maybe_initialize_telegram_app
from app.supbot.utils.aiogram_ext import TelegramApp

telegram_app = TelegramApp()

telegram_app.include_router(error_handling_tgm.router)
telegram_app.include_router(start_tgm.router)
telegram_app.include_router(vacancy_tgm.router)
telegram_app.include_router(support_tgm.router)
telegram_app.include_router(support_team_tgm.router)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    await maybe_initialize_telegram_app(telegram_app)
    yield


api_router = APIRouterExt(prefix="/api/telegram", lifespan=lifespan)


@api_router.post(
    "/updates/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Execute telegram webhook",
)
async def feed_update_from_telegram(request: Request) -> None:
    await telegram_app.dispatcher.feed_webhook_update(
        telegram_app.bot, await request.json()
    )
