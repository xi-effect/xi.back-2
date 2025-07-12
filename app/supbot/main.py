from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.supbot.config import telegram_app
from app.supbot.routers import (
    error_handling_tgm,
    start_tgm,
    support_team_tgm,
    support_tgm,
    telegram_webhook_rst,
    vacancy_tgm,
)
from app.supbot.texts import BOT_COMMANDS

telegram_app.include_router(error_handling_tgm.router)
telegram_app.include_router(start_tgm.router)
telegram_app.include_router(vacancy_tgm.router)
telegram_app.include_router(support_tgm.router)
telegram_app.include_router(support_team_tgm.router)

outside_router = APIRouterExt(prefix="/api/public/supbot-service")
outside_router.include_router(telegram_webhook_rst.router)

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/supbot-service",
)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/supbot-service",
)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/supbot-service",
)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    await telegram_app.maybe_initialize_from_config(
        bot_name="supbot",
        bot_settings=settings.supbot,
        bot_commands=BOT_COMMANDS,
        webhook_prefix=outside_router.prefix,
        group_id=settings.supbot and settings.supbot.group_id,
    )
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(mub_router)
api_router.include_router(internal_router)
