from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt

outside_router = APIRouterExt(prefix="/api/public/conference-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/conference-service",
)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/conference-service",
)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/conference-service",
)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(mub_router)
api_router.include_router(internal_router)
