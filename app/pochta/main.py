import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.pochta.routes import pochta_mub

outside_router = APIRouterExt(prefix="/api/public/pochta-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/pochta-service",
)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/pochta-service",
)

mub_router = APIRouterExt(prefix="/mub/pochta-service", dependencies=[MUBProtection])
mub_router.include_router(pochta_mub.router)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    if settings.production_mode and settings.email is None:
        logging.warning("Configuration for email service is missing")
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(internal_router)
api_router.include_router(mub_router)
