from typing import Any

import pytest
from pytest_lazy_fixtures import lf

from app.notifications.models.delivery_methods_db import (
    TelegramDeliveryMethod,
    VKDeliveryMethod,
)
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services.user_contact_syncers import (
    base_user_contact_syncer,
    telegram_user_contact_syncer,
    vk_user_contact_syncer,
)
from tests.common.active_session import ActiveSession

pytestmark = pytest.mark.anyio


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


@pytest.mark.parametrize(
    ("user_contact_syncer", "existing_user_contact"),
    [
        pytest.param(
            lf("active_telegram_user_contact_syncer"),
            None,
            id="personal_telegram-no_user_contact",
        ),
        pytest.param(
            lf("active_telegram_user_contact_syncer"),
            lf("personal_telegram_user_contact"),
            id="personal_telegram-with_user_contact",
        ),
        pytest.param(
            lf("active_vk_user_contact_syncer"),
            None,
            id="personal_vk-no_user_contact",
        ),
        pytest.param(
            lf("active_vk_user_contact_syncer"),
            lf("personal_vk_user_contact"),
            id="personal_vk-with_user_contact",
        ),
    ],
)
async def test_messenger_user_contact_removing(
    active_session: ActiveSession,
    user_contact_syncer: base_user_contact_syncer.BaseUserContactSyncer[Any],
    existing_user_contact: UserContact | None,
) -> None:
    async with active_session():
        await user_contact_syncer.remove()

    async with active_session():
        assert (
            await UserContact.find_first_by_primary_key(
                user_id=user_contact_syncer.delivery_method.user_id,
                kind=user_contact_syncer.contact_kind,
            )
        ) is None
