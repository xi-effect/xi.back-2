from collections.abc import AsyncIterator

import pytest
from faststream.redis import RedisBroker, TestRedisBroker

from app.main import faststream


@pytest.fixture(scope="session", autouse=True)
async def faststream_broker() -> AsyncIterator[RedisBroker]:
    async with TestRedisBroker(faststream.broker) as broker:
        yield broker
