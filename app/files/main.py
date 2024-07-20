from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.files.routes import files_mub, files_rst

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/file-service",
)

authorized_router.include_router(files_rst.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/file-service",
)

mub_router.include_router(files_mub.router)

router = APIRouterExt()
router.include_router(authorized_router)
router.include_router(mub_router)
