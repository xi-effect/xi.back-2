from aiogram.utils.link import create_telegram_link

from app.common.aiogram_ext import MessageFromUser
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.config import telegram_app
from app.notifications.models.delivery_methods_db import TelegramDeliveryMethod
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services.user_contact_syncers.base_user_contact_syncer import (
    BaseUserContactSyncer,
)


class TelegramUserContactSyncer(BaseUserContactSyncer[TelegramDeliveryMethod]):
    contact_kind = UserContactKind.PERSONAL_TELEGRAM

    def username_to_link(self, username: str) -> str:
        return create_telegram_link(username)

    async def sync_from_message(self, message: MessageFromUser) -> UserContact | None:
        if message.from_user.username is None:
            return None
        return await self.upsert_from_username(username=message.from_user.username)

    async def retrieve_current_username(self) -> str | None:
        chat_member = await telegram_app.bot.get_chat_member(
            chat_id=self.delivery_method.peer_id,
            user_id=self.delivery_method.peer_id,  # matches for private chats
        )
        return chat_member.user.username
