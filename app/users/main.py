from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends

from app.common.config import settings
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.users.routes import (
    avatar_rst,
    current_user_rst,
    email_confirmation_rst,
    forms_rst,
    onboarding_rst,
    password_reset_rst,
    proxy_rst,
    reglog_rst,
    sessions_mub,
    sessions_rst,
    users_mub,
    users_rst,
)
from app.users.utils.authorization import authorize_user

outside_router = APIRouterExt(prefix="/api/public/user-service")
outside_router.include_router(reglog_rst.router)
outside_router.include_router(forms_rst.router)
outside_router.include_router(email_confirmation_rst.router)
outside_router.include_router(password_reset_rst.router)

authorized_router = APIRouterExt(
    dependencies=[Depends(authorize_user)],
    prefix="/api/protected/user-service",
)
authorized_router.include_router(onboarding_rst.router)
authorized_router.include_router(users_rst.router)
authorized_router.include_router(current_user_rst.router)
authorized_router.include_router(avatar_rst.router)
authorized_router.include_router(sessions_rst.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/user-service",
)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/user-service",
)
mub_router.include_router(users_mub.router)
mub_router.include_router(sessions_mub.router)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    settings.avatars_path.mkdir(exist_ok=True)
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(internal_router)
api_router.include_router(mub_router)
api_router.include_router(proxy_rst.router)
