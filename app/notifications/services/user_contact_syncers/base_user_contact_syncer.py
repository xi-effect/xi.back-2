from abc import ABC, abstractmethod
from typing import ClassVar

from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.models.delivery_methods_db import MessengerDeliveryMethod
from app.notifications.models.user_contacts_db import UserContact


class BaseUserContactSyncer[DeliveryMethodType: MessengerDeliveryMethod](ABC):
    contact_kind: ClassVar[UserContactKind]

    def __init__(self, delivery_method: DeliveryMethodType) -> None:
        self.delivery_method = delivery_method

    async def remove(self) -> None:
        await UserContact.delete_by_primary_key(
            user_id=self.delivery_method.user_id,
            kind=self.contact_kind,
        )

    @abstractmethod
    def username_to_link(self, username: str) -> str:
        raise NotImplementedError

    async def upsert_from_username(self, username: str) -> UserContact:
        return await UserContact.upsert(
            user_id=self.delivery_method.user_id,
            kind=self.contact_kind,
            link=self.username_to_link(username=username),
            title=f"@{username}",
        )

    @abstractmethod
    async def retrieve_current_username(self) -> str | None:
        raise NotImplementedError

    async def sync_with_origin(self) -> UserContact | None:
        username = await self.retrieve_current_username()

        if username is None:
            await self.remove()
            return None

        return await self.upsert_from_username(
            username=username,
        )
