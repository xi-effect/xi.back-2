from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from tmexio import EventRouter

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.messenger.routes import (
    chats_int,
    chats_sio,
    messages_management_sio,
    messages_mub,
    my_messages_sio,
)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/messenger-service",
)
internal_router.include_router(chats_int.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/messenger-service",
)
mub_router.include_router(messages_mub.router)

api_router = APIRouterExt()
api_router.include_router(internal_router)
api_router.include_router(mub_router)

event_router = EventRouter()
event_router.include_router(chats_sio.router)
event_router.include_router(my_messages_sio.router)
event_router.include_router(messages_management_sio.router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    yield
