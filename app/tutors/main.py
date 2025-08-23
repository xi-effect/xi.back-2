from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import ProxyAuthorized
from app.common.dependencies.mub_dep import MUBProtection
from app.common.fastapi_ext import APIRouterExt
from app.tutors.routes import (
    classrooms_tutor_rst,
    invitations_student_rst,
    invitations_tutor_rst,
    materials_tutor_rst,
    subjects_mub,
    tutorships_mub,
    tutorships_student_rst,
    tutorships_tutor_rst,
)

outside_router = APIRouterExt(prefix="/api/public/tutor-service")

authorized_router = APIRouterExt(
    dependencies=[ProxyAuthorized],
    prefix="/api/protected/tutor-service",
)
authorized_router.include_router(invitations_tutor_rst.router)
authorized_router.include_router(invitations_student_rst.router)
authorized_router.include_router(materials_tutor_rst.router)
authorized_router.include_router(tutorships_tutor_rst.router)
authorized_router.include_router(tutorships_student_rst.router)
authorized_router.include_router(classrooms_tutor_rst.router)

mub_router = APIRouterExt(
    dependencies=[MUBProtection],
    prefix="/mub/tutor-service",
)
mub_router.include_router(subjects_mub.router)
mub_router.include_router(tutorships_mub.router)

internal_router = APIRouterExt(
    dependencies=[APIKeyProtection],
    prefix="/internal/tutor-service",
)


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
    yield


api_router = APIRouterExt(lifespan=lifespan)
api_router.include_router(outside_router)
api_router.include_router(authorized_router)
api_router.include_router(mub_router)
api_router.include_router(internal_router)
