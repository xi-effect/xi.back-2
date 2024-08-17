from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.posts.routes import post_channels_int, posts_mub

outside_router = APIRouterExt(prefix="/api/public/post-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/post-service",
)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/post-service",
)
mub_router.include_router(posts_mub.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/post-service",
)
internal_router.include_router(post_channels_int.router)

router = APIRouterExt()
router.include_router(outside_router)
router.include_router(authorized_router)
router.include_router(mub_router)
router.include_router(internal_router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    yield
