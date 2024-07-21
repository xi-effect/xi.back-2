import logging
from collections.abc import AsyncIterator

from tmexio import EventRouter, register_dependency
from tmexio.handler_builders import Depends

from app.common.config import sessionmaker
from app.common.sqlalchemy_ext import session_context


@register_dependency()
async def db_session() -> AsyncIterator[None]:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        yield


class EventRouterExt(EventRouter):
    def __init__(
        self,
        dependencies: list[Depends] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        super().__init__(dependencies=[db_session] + (dependencies or []), tags=tags)


class NoPingPongFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: FNE005
        return not (
            "Received packet PONG" in record.getMessage()
            or "Sending packet PING" in record.getMessage()
        )


def remove_ping_pong_logs() -> None:
    logging.getLogger("engineio.server").addFilter(NoPingPongFilter())
