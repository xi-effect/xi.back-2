from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.common.config import STORAGE_PATH
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.storage.models.files_db import FILE_KIND_TO_FOLDER
from app.storage.routers import files_rst

outside_router = APIRouterExt(prefix="/api/public/storage-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/storage-service",
)
authorized_router.include_router(files_rst.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/storage-service",
)

router = APIRouterExt()
router.include_router(outside_router)
router.include_router(authorized_router)
router.include_router(mub_router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    STORAGE_PATH.mkdir(exist_ok=True)
    for sub_folder in FILE_KIND_TO_FOLDER.values():
        (STORAGE_PATH / sub_folder).mkdir(exist_ok=True)
    yield
