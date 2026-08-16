import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from faststream.redis import RedisRouter

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.notifications.config import telegram_app, vk_app
from app.notifications.routes import (
    delivery_methods_int,
    delivery_methods_rst,
    delivery_methods_tgm,
    disabled_delivery_routes_rst,
    notifications_mub,
    notifications_rst,
    notifications_sub,
    telegram_webhook_rst,
    user_contacts_int,
    user_contacts_mub,
    user_contacts_rst,
    vk_webhook_rst,
)

telegram_app.include_router(delivery_methods_tgm.router)

stream_router = RedisRouter()
stream_router.include_router(notifications_sub.router)

outside_router = APIRouterExt(prefix="/api/public/notification-service")
outside_router.include_router(telegram_webhook_rst.router)
outside_router.include_router(vk_webhook_rst.router)

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/notification-service",
)
authorized_router.include_router(delivery_methods_rst.router)
authorized_router.include_router(disabled_delivery_routes_rst.router)
authorized_router.include_router(notifications_rst.router)
authorized_router.include_router(user_contacts_rst.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/notification-service",
)
mub_router.include_router(notifications_mub.router)
mub_router.include_router(user_contacts_mub.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/notification-service",
)
internal_router.include_router(delivery_methods_int.router)
internal_router.include_router(user_contacts_int.router)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    try:
        await telegram_app.maybe_initialize_from_config(
            bot_name="notifications bot",
            bot_settings=settings.telegram_notifications_bot,
            webhook_prefix=outside_router.prefix,
        )
    except Exception as e:  # pragma: no cover  # setup-level safety
        logging.error("Telegram notifications bot initialization failed", exc_info=e)

    try:
        await vk_app.maybe_initialize_from_config(
            bot_name="notifications bot",
            bot_settings=settings.vk_notifications_bot,
            webhook_prefix=outside_router.prefix,
        )
    except Exception as e:  # pragma: no cover  # setup-level safety
        logging.error("VK notifications bot initialization failed", exc_info=e)

    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(mub_router)
api_router.include_router(internal_router)
