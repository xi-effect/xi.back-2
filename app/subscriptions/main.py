from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.subscriptions.routes import promocodes_mub

outside_router = APIRouterExt(prefix="/api/public/subscription-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/subscription-service",
)

mub_router = APIRouterExt(
    dependencies=[MUBProtection], prefix="/mub/subscription-service"
)
mub_router.include_router(promocodes_mub.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/subscription-service",
)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(mub_router)
api_router.include_router(internal_router)
