from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from faststream.redis import RedisRouter

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.datalake.routes import datalake_events_mub, datalake_events_sub

outside_router = APIRouterExt(prefix="/api/public/datalake-service")

stream_router = RedisRouter()
stream_router.include_router(datalake_events_sub.router)

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/datalake-service",
)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/datalake-service",
)

mub_router = APIRouterExt(prefix="/mub/datalake-service", dependencies=[MUBProtection])
mub_router.include_router(datalake_events_mub.router)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(internal_router)
api_router.include_router(mub_router)
