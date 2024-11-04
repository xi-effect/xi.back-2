from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from tmexio import EventRouter

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.fastapi_ext import APIRouterExt
from app.messenger.routes import chats_int

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/messenger-service",
)
internal_router.include_router(chats_int.router)

api_router = APIRouterExt()
api_router.include_router(internal_router)

event_router = EventRouter()


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    yield
