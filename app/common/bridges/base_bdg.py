from contextlib import AsyncExitStack

from faststream.redis import RedisBroker
from httpx import AsyncClient


class BaseBridge:
    def __init__(
        self,
        *,
        base_url: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.client = AsyncClient(base_url=base_url, headers=headers)
        self._broker: RedisBroker | None = None

    @property
    def broker(self) -> RedisBroker:
        if self._broker is None:
            raise EnvironmentError("Broker is not initialized")
        return self._broker

    async def setup(self, exit_stack: AsyncExitStack, broker: RedisBroker) -> None:
        await exit_stack.enter_async_context(self.client)
        self._broker = broker
