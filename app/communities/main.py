from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from tmexio import EventRouter

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.communities.routes import (
    avatars_rst,
    board_channels_int,
    board_channels_mub,
    board_channels_sio,
    categories_mub,
    categories_sio,
    channels_mub,
    channels_sio,
    communities_mub,
    communities_public_rst,
    communities_sio,
    invitations_mub,
    invitations_sio,
    participants_mub,
    participants_sio,
    tasks_mub,
)

outside_router = APIRouterExt(prefix="/api/public/community-service")
outside_router.include_router(communities_public_rst.router)

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/community-service",
)
authorized_router.include_router(avatars_rst.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/community-service",
)
internal_router.include_router(board_channels_int.router)


mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/community-service",
)
mub_router.include_router(communities_mub.router)
mub_router.include_router(invitations_mub.router)
mub_router.include_router(participants_mub.router)
mub_router.include_router(categories_mub.router)
mub_router.include_router(channels_mub.router)
mub_router.include_router(board_channels_mub.router)
mub_router.include_router(tasks_mub.router)

api_router = APIRouterExt()
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(internal_router)
api_router.include_router(mub_router)

event_router = EventRouter()
event_router.include_router(communities_sio.router)
event_router.include_router(invitations_sio.router)
event_router.include_router(participants_sio.router)
event_router.include_router(categories_sio.router)
event_router.include_router(channels_sio.router)
event_router.include_router(board_channels_sio.router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    settings.community_avatars_path.mkdir(exist_ok=True)
    yield
