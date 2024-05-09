import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response
from tmexio import TMEXIO, AsyncSocket, EventException

from app import communities
from app.common.config import (
    AVATARS_PATH,
    DATABASE_MIGRATED,
    PRODUCTION_MODE,
    Base,
    engine,
    sessionmaker,
)
from app.common.dependencies.authorization_dep import authorize_from_wsgi_environ
from app.common.sqlalchemy_ext import session_context
from app.common.starlette_cors_ext import CorrectCORSMiddleware

tmex = TMEXIO(
    async_mode="asgi",
    transports=["websocket"],
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)


class NoPingPongFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: FNE005
        return not (
            "Received packet PONG" in record.getMessage()
            or "Sending packet PING" in record.getMessage()
        )


logging.getLogger("engineio.server").addFilter(NoPingPongFilter())


@tmex.on_connect()
async def connect_user(socket: AsyncSocket) -> None:
    try:
        auth_data = await authorize_from_wsgi_environ(socket.get_environ())
    except ValidationError:
        raise EventException(407, "bad")
    await socket.save_session({"auth": auth_data})
    await socket.enter_room(f"user-{auth_data.user_id}")


async def reinit_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    AVATARS_PATH.mkdir(exist_ok=True)

    if not PRODUCTION_MODE and not DATABASE_MIGRATED:
        await reinit_database()

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CorrectCORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/socket.io/", tmex.build_asgi_app())

app.include_router(communities.router)


@app.middleware("http")
async def database_session_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        return await call_next(request)
