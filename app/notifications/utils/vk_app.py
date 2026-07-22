import logging

from app.common.config import VKBotSettings, settings
from app.notifications.utils.vk_client import VKClient


class VKApp:
    def __init__(self) -> None:
        self._client: VKClient | None = None

    async def initialize(self, client: VKClient) -> None:
        self._client = client

    @property
    def client(self) -> VKClient:
        if self._client is None:
            raise EnvironmentError("Client is not initialized")
        return self._client

    async def maybe_initialize_from_config(
        self,
        *,
        bot_name: str,
        bot_settings: VKBotSettings | None,
        webhook_prefix: str,
        webhook_path: str = "/vk-updates/",
    ) -> None:
        if settings.is_testing_mode or bot_settings is None:
            if settings.production_mode:
                logging.error(f"Configuration for VK bot '{bot_name}' is missing")
            return

        await self.initialize(
            client=VKClient(
                base_url=settings.vk_server_base_url,
                api_token=bot_settings.api_token,
                group_id=bot_settings.group_id,
            )
        )
        # TODO also enter context for `VKClient`

        _ = webhook_path, webhook_prefix  # noqa: WPS122
        # TODO setup webhook / polling automatically
