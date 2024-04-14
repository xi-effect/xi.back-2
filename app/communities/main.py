from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt

outside_router = APIRouterExt()

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/communities",
)


mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/communities",
)


router = APIRouterExt()
router.include_router(outside_router)
router.include_router(authorized_router)
router.include_router(mub_router)
