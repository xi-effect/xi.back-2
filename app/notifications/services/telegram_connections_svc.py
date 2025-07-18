from app.notifications.config import telegram_app
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)


async def retrieve_telegram_username_by_user_id(user_id: int) -> str | None:
    telegram_connection = await TelegramConnection.find_first_by_user_id_and_status(
        user_id=user_id, allowed_statuses=[TelegramConnectionStatus.ACTIVE]
    )
    if telegram_connection is None:
        return None

    chat_member = await telegram_app.bot.get_chat_member(
        chat_id=telegram_connection.chat_id,
        user_id=telegram_connection.chat_id,  # matches for private chats
    )
    return chat_member.user.username
