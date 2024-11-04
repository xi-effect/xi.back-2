from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from tmexio import EventRouter

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.fastapi_ext import APIRouterExt

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/messenger-service",
)

api_router = APIRouterExt()
api_router.include_router(internal_router)

event_router = EventRouter()


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    yield
