from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.communities.routes import (
    avatars_rst,
    communities_mub,
    invitations_mub,
    participants_mub,
)

outside_router = APIRouterExt(prefix="/api/public/community-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/community-service",
)
authorized_router.include_router(avatars_rst.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/community-service",
)
mub_router.include_router(communities_mub.router)
mub_router.include_router(invitations_mub.router)
mub_router.include_router(participants_mub.router)


router = APIRouterExt()
router.include_router(outside_router)
router.include_router(authorized_router)
router.include_router(mub_router)
