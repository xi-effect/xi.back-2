import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.common.config import settings
from app.common.fastapi_ext import APIRouterExt
from app.pochta.routes import pochta_mub
from app.users.utils.mub import MUBProtection

mub_router = APIRouterExt(prefix="/mub", dependencies=[MUBProtection])
mub_router.include_router(pochta_mub.router, prefix="/pochta-service")


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    if settings.production_mode and settings.email is None:
        logging.warning("Configuration for email service is missing")
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(mub_router)
