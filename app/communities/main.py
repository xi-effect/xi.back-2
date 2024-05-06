from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.communities.routes import communities_mub

outside_router = APIRouterExt(prefix="/api/public/community-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/community-service",
)


mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/community-service",
)
mub_router.include_router(communities_mub.router)


router = APIRouterExt()
router.include_router(outside_router)
router.include_router(authorized_router)
router.include_router(mub_router)
