from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app import communities, posts, storage
from app.common.config import (
    DATABASE_MIGRATED,
    PRODUCTION_MODE,
    Base,
    engine,
    sessionmaker,
)
from app.common.config_bdg import posts_bridge
from app.common.sqlalchemy_ext import session_context
from app.common.starlette_cors_ext import CorrectCORSMiddleware


async def reinit_database() -> None:  # pragma: no cover
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if not PRODUCTION_MODE and not DATABASE_MIGRATED:
        await reinit_database()

    async with AsyncExitStack() as stack:
        await stack.enter_async_context(communities.lifespan())
        await stack.enter_async_context(posts.lifespan())
        await stack.enter_async_context(storage.lifespan())

        await posts_bridge.open_if_unopen(stack)

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

app.include_router(communities.router)
app.include_router(posts.router)
app.include_router(storage.router)


@app.middleware("http")
async def database_session_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        return await call_next(request)
