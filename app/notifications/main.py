from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from faststream.redis import RedisRouter

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.notifications.config import telegram_app
from app.notifications.routes import (
    notification_settings_rst,
    notifications_mub,
    notifications_rst,
    notifications_sub,
    telegram_connections_mub,
    telegram_connections_rst,
    telegram_connections_tgm,
    telegram_webhook_rst,
    user_contacts_int,
    user_contacts_mub,
    user_contacts_rst,
)

telegram_app.include_router(telegram_connections_tgm.router)

stream_router = RedisRouter()
stream_router.include_router(notifications_sub.router)

outside_router = APIRouterExt(prefix="/api/public/notification-service")
outside_router.include_router(telegram_webhook_rst.router)

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/notification-service",
)
authorized_router.include_router(notification_settings_rst.router)
authorized_router.include_router(notifications_rst.router)
authorized_router.include_router(telegram_connections_rst.router)
authorized_router.include_router(user_contacts_rst.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/notification-service",
)
mub_router.include_router(notifications_mub.router)
mub_router.include_router(telegram_connections_mub.router)
mub_router.include_router(user_contacts_mub.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/notification-service",
)
internal_router.include_router(user_contacts_int.router)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    await telegram_app.maybe_initialize_from_config(
        bot_name="notifications bot",
        bot_settings=settings.notifications_bot,
        webhook_prefix=outside_router.prefix,
    )
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(mub_router)
api_router.include_router(internal_router)
