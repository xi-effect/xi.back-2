from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf

from app.notifications.dependencies.delivery_methods_dep import (
    AnyMessengerDeliveryMethod,
)
from app.notifications.services import user_contacts_svc
from app.notifications.services.user_contact_syncers import (
    base_user_contact_syncer,
    telegram_user_contact_syncer,
    vk_user_contact_syncer,
)

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("delivery_method", "expected_user_contact_syncer_type"),
    [
        pytest.param(
            lf("active_telegram_delivery_method"),
            telegram_user_contact_syncer.TelegramUserContactSyncer,
            id="telegram",
        ),
        pytest.param(
            lf("active_vk_delivery_method"),
            vk_user_contact_syncer.VKUserContactSyncer,
            id="vk",
        ),
    ],
)
async def test_user_contact_syncer_converting(
    delivery_method: AnyMessengerDeliveryMethod,
    expected_user_contact_syncer_type: type[
        base_user_contact_syncer.BaseUserContactSyncer[Any]
    ],
) -> None:
    user_contact_syncer = user_contacts_svc.delivery_method_to_user_contact_syncer(
        delivery_method=delivery_method,
    )

    assert isinstance(user_contact_syncer, expected_user_contact_syncer_type)
    assert_contains(user_contact_syncer, {"delivery_method": delivery_method})
