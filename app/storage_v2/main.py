from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.storage_v2.models.files_db import FILE_KIND_TO_FOLDER
from app.storage_v2.routers import (
    access_groups_int,
    files_rst,
    ydocs_hocus_int,
    ydocs_meta_int,
)

outside_router = APIRouterExt(prefix="/api/public/storage-service/v2")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/storage-service/v2",
)
authorized_router.include_router(files_rst.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/storage-service/v2",
)
internal_router.include_router(access_groups_int.router)
internal_router.include_router(ydocs_meta_int.router)
internal_router.include_router(ydocs_hocus_int.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/storage-service/v2",
)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    settings.storage_path.mkdir(exist_ok=True)
    for sub_folder in FILE_KIND_TO_FOLDER.values():
        (settings.storage_path / sub_folder).mkdir(exist_ok=True)
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(internal_router)
api_router.include_router(mub_router)
