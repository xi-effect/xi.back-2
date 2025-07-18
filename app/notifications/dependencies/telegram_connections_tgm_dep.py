from typing import Any

from aiogram.filters import Filter

from app.common.aiogram_ext import ChatMemberUpdatedExt, MessageExt
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)


class TelegramConnectionFilter(Filter):
    def __init__(self, connection_status: TelegramConnectionStatus) -> None:
        self.connection_status = connection_status

    async def __call__(  # noqa: FNE005
        self,
        event: MessageExt | ChatMemberUpdatedExt,
    ) -> bool | dict[str, Any]:
        telegram_connection = await TelegramConnection.find_first_by_chat_id_and_status(
            chat_id=event.chat.id,
            allowed_statuses=[self.connection_status],
        )
        if telegram_connection is None:
            return False
        return {"telegram_connection": telegram_connection}
