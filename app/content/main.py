from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.common.utils.mimetypes import add_missing_mime_to_mimetypes
from app.content.routes import (
    classroom_materials_student_rst,
    classroom_materials_tutor_rst,
    classroom_notes_tutor_rst,
    files_rst,
    materials_tutor_rst,
    personal_materials_tutor_rst,
    ydocs_int,
)

outside_router = APIRouterExt(prefix="/api/public/content-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/content-service",
)
authorized_router.include_router(files_rst.router)
authorized_router.include_router(materials_tutor_rst.router)
authorized_router.include_router(personal_materials_tutor_rst.router)
authorized_router.include_router(classroom_materials_tutor_rst.router)
authorized_router.include_router(classroom_materials_student_rst.router)
authorized_router.include_router(classroom_notes_tutor_rst.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/content-service",
)
internal_router.include_router(ydocs_int.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/content-service",
)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    (settings.storage_path / "files").mkdir(parents=True, exist_ok=True)
    add_missing_mime_to_mimetypes()
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(internal_router)
api_router.include_router(mub_router)
