from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.scheduler.routes import events_mub

outside_router = APIRouterExt(prefix="/api/public/scheduler-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/scheduler-service",
)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/scheduler-service",
)
mub_router.include_router(events_mub.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/scheduler-service",
)

api_router = APIRouterExt()
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(mub_router)
api_router.include_router(internal_router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    yield
