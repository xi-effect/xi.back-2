from app.notifications.config import telegram_app
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    TelegramDeliveryMethod,
)


async def retrieve_telegram_username_by_user_id(user_id: int) -> str | None:
    delivery_method = await TelegramDeliveryMethod.find_first_by_user_id_and_status(
        user_id=user_id,
        allowed_statuses=[DeliveryMethodStatus.ACTIVE],
    )
    if delivery_method is None:
        return None

    chat_member = await telegram_app.bot.get_chat_member(
        chat_id=delivery_method.peer_id,
        user_id=delivery_method.peer_id,  # matches for private chats
    )
    return chat_member.user.username
