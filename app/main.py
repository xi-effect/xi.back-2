from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Annotated, Any

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from faststream import BaseMiddleware, StreamMessage
from faststream.redis.fastapi import RedisRouter
from pydantic import ValidationError
from starlette import status
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from tmexio import AsyncSocket, EventException, EventName, PydanticPackager
from tmexio.documentation import OpenAPIBuilder

from app import (
    autocomplete,
    classrooms,
    communities,
    conferences,
    invoices,
    materials,
    messenger,
    notifications,
    payments,
    pochta,
    posts,
    scheduler,
    storage_v2,
    supbot,
    users,
)
from app.common.config import Base, engine, livekit, sessionmaker, settings, tmex
from app.common.config_bdg import all_bridges
from app.common.dependencies.authorization_sio_dep import authorize_from_wsgi_environ
from app.common.sqlalchemy_ext import session_context
from app.common.starlette_cors_ext import CorrectCORSMiddleware
from app.common.tmexio_ext import remove_ping_pong_logs
from app.communities.rooms import user_room
from app.communities.store import user_id_to_sids

tmex.include_router(communities.event_router)
tmex.include_router(messenger.event_router)
remove_ping_pong_logs()

if settings.socketio_admin is not None:
    tmex.backend.instrument(
        auth={
            "username": settings.socketio_admin.username,
            "password": settings.socketio_admin.password,
        },
        mode=(
            "production"
            if settings.socketio_admin.is_production_mode
            else "development"
        ),
        read_only=settings.socketio_admin.is_read_only,
        server_id=settings.instance_name,
        namespace=settings.socketio_admin.namespace_name,
        server_stats_interval=settings.socketio_admin.server_stats_interval,
    )


@tmex.on_connect(summary="[special] Automatic event")
async def connect_user(socket: AsyncSocket) -> None:
    try:
        auth_data = await authorize_from_wsgi_environ(socket.get_environ())
    except ValidationError:  # TODO (38980978) pragma: no cover
        raise EventException(status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED, "bad")
    await socket.save_session({"auth": auth_data})
    user_id_to_sids[auth_data.user_id].add(socket.sid)
    await socket.enter_room(user_room(auth_data.user_id))


@tmex.on_disconnect(summary="[special] Automatic event")
async def disconnect_user(socket: AsyncSocket) -> None:
    user_id = (await socket.get_session())["auth"].user_id
    user_id_to_sids[user_id].remove(socket.sid)


@tmex.on_other(summary="[special] Handler for non-existent events")
async def handle_other_events(  # TODO (38980978) pragma: no cover
    event_name: EventName,
) -> Annotated[str, PydanticPackager(str, status.HTTP_404_NOT_FOUND)]:
    return f"Unknown event: '{event_name}'"


class FastStreamDatabaseSessionMiddleware(BaseMiddleware):
    async def consume_scope(
        self,
        call_next: Callable[[Any], Awaitable[Any]],
        msg: StreamMessage[Any],
    ) -> Any:
        async with sessionmaker.begin() as session:
            session_context.set(session)
            return await call_next(msg)


faststream = RedisRouter(
    settings.redis_faststream_dsn,
    middlewares=[FastStreamDatabaseSessionMiddleware],
)
faststream.include_router(notifications.stream_router)  # type: ignore[arg-type]
faststream.include_router(pochta.stream_router)  # type: ignore[arg-type]


async def reinit_database() -> None:  # pragma: no cover
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.postgres_automigrate:
        await reinit_database()

    async with AsyncExitStack() as stack:
        for bridge in all_bridges:
            await bridge.setup(exit_stack=stack, broker=faststream.broker)

        await stack.enter_async_context(livekit)

        yield


app = FastAPI(
    title="xi.back-2",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> Response:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="xi.back-2",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url=(
            '/static/favicon-for-light.svg">\n'
            + '<link rel="icon" href="/static/favicon-for-dark.svg" '
            + 'media="(prefers-color-scheme: dark)'
        ),
    )


app.add_middleware(
    CorrectCORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(faststream)
app.mount("/socket.io/", tmex.build_asgi_app())

include_unused_services = not settings.production_mode
app.include_router(autocomplete.api_router)
app.include_router(communities.api_router, include_in_schema=include_unused_services)
app.include_router(conferences.api_router)
app.include_router(invoices.api_router)
app.include_router(materials.api_router)
app.include_router(messenger.api_router, include_in_schema=include_unused_services)
app.include_router(notifications.api_router)
app.include_router(payments.api_router)
app.include_router(pochta.api_router)
app.include_router(posts.api_router, include_in_schema=include_unused_services)
app.include_router(scheduler.api_router)
app.include_router(storage_v2.api_router)
app.include_router(supbot.api_router)
app.include_router(classrooms.api_router)
app.include_router(users.api_router)

old_openapi = app.openapi


def custom_openapi() -> Any:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = old_openapi()
    openapi_schema["openapi"] = "3.0.1"
    # for some reason other versions don't render generated TMEXIO refs properly
    # but the handwritten api schema worked fine on 3.1.0
    # also 204s without body are not rendered correctly on 3.1.0

    builder = OpenAPIBuilder(tmex, model_prefix="tmexio_")
    tmex_api_schema = builder.build_documentation()

    openapi_schema["paths"].update(tmex_api_schema["paths"])
    openapi_schema["components"]["schemas"].update(
        tmex_api_schema["components"]["schemas"]
    )

    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]  # from fastapi docs (dumb)


@app.middleware("http")
async def database_session_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        return await call_next(request)
