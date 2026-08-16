from typing import Any, assert_never

from app.notifications.dependencies.delivery_methods_dep import (
    AnyMessengerDeliveryMethod,
)
from app.notifications.models.delivery_methods_db import (
    TelegramDeliveryMethod,
    VKDeliveryMethod,
)
from app.notifications.services.user_contact_syncers import (
    base_user_contact_syncer,
    telegram_user_contact_syncer,
    vk_user_contact_syncer,
)


def delivery_method_to_user_contact_syncer(
    delivery_method: AnyMessengerDeliveryMethod,
) -> base_user_contact_syncer.BaseUserContactSyncer[Any]:
    match delivery_method:
        case TelegramDeliveryMethod():
            return telegram_user_contact_syncer.TelegramUserContactSyncer(
                delivery_method=delivery_method
            )
        case VKDeliveryMethod():
            return vk_user_contact_syncer.VKUserContactSyncer(
                delivery_method=delivery_method
            )
        case _:
            assert_never(delivery_method)
