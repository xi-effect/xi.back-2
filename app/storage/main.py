from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.storage.models.files_db import FILE_KIND_TO_FOLDER
from app.storage.routers import access_groups_int, files_rst, ydocs_int

outside_router = APIRouterExt(prefix="/api/public/storage-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/storage-service",
)
authorized_router.include_router(files_rst.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/storage-service",
)
internal_router.include_router(access_groups_int.router)
internal_router.include_router(ydocs_int.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/storage-service",
)

api_router = APIRouterExt()
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(internal_router)
api_router.include_router(mub_router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    settings.storage_path.mkdir(exist_ok=True)
    for sub_folder in FILE_KIND_TO_FOLDER.values():
        (settings.storage_path / sub_folder).mkdir(exist_ok=True)
    yield
