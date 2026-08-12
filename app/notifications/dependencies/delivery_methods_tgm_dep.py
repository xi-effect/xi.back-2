from typing import Any

from aiogram.filters import Filter

from app.common.aiogram_ext import ChatMemberUpdatedExt, MessageExt
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    TelegramDeliveryMethod,
)


class TelegramDeliveryMethodFilter(Filter):
    def __init__(self, expected_status: DeliveryMethodStatus) -> None:
        self.expected_status = expected_status

    async def __call__(  # noqa: FNE005
        self,
        event: MessageExt | ChatMemberUpdatedExt,
    ) -> bool | dict[str, Any]:
        delivery_method = await TelegramDeliveryMethod.find_first_by_peer_id_and_status(
            peer_id=event.chat.id,
            allowed_statuses=[self.expected_status],
        )
        if delivery_method is None:
            return False
        return {"delivery_method": delivery_method}
