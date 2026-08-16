import pytest

from app.notifications.models.delivery_methods_db import (
    TelegramDeliveryMethod,
    VKDeliveryMethod,
)
from app.notifications.services.user_contact_syncers import (
    telegram_user_contact_syncer,
    vk_user_contact_syncer,
)


@pytest.fixture()
async def active_telegram_user_contact_syncer(
    active_telegram_delivery_method: TelegramDeliveryMethod,
) -> telegram_user_contact_syncer.TelegramUserContactSyncer:
    return telegram_user_contact_syncer.TelegramUserContactSyncer(
        delivery_method=active_telegram_delivery_method
    )


@pytest.fixture()
async def active_vk_user_contact_syncer(
    active_vk_delivery_method: VKDeliveryMethod,
) -> vk_user_contact_syncer.VKUserContactSyncer:
    return vk_user_contact_syncer.VKUserContactSyncer(
        delivery_method=active_vk_delivery_method
    )
