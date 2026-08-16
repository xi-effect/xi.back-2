from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.config import vk_app
from app.notifications.models.delivery_methods_db import VKDeliveryMethod
from app.notifications.services.user_contact_syncers.base_user_contact_syncer import (
    BaseUserContactSyncer,
)


class VKUserContactSyncer(BaseUserContactSyncer[VKDeliveryMethod]):
    contact_kind = UserContactKind.PERSONAL_VK

    def username_to_link(self, username: str) -> str:
        return f"https://vk.ru/{username}"

    async def retrieve_current_username(self) -> str | None:
        user_data = await vk_app.client.get_user(user_id=self.delivery_method.peer_id)
        if user_data is None:
            return None
        return user_data.screen_name
