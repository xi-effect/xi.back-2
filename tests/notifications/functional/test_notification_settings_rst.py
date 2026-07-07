import random

import pytest
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    TelegramDeliveryMethod,
)
from app.notifications.models.user_contacts_db import UserContact
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.notifications.factories import UserContactInputFactory

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("has_telegram_delivery_method", "has_personal_telegram_contact"),
    [
        pytest.param(False, False, id="no_telegram"),
        pytest.param(
            True, False, id="with_telegram_delivery_method-no_telegram_contact"
        ),
        pytest.param(
            True, True, id="with_telegram_delivery_method-with_telegram_contact"
        ),
    ],
)
async def test_retrieving_notification_settings(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    tg_chat_id: int,
    has_telegram_delivery_method: bool,
    has_personal_telegram_contact: bool,
) -> None:
    async with active_session():
        if has_telegram_delivery_method:
            delivery_method_data = {"status": random.choice(list(DeliveryMethodStatus))}
            await TelegramDeliveryMethod.create(
                user_id=proxy_auth_data.user_id,
                peer_id=tg_chat_id,
                **delivery_method_data,
            )
        else:
            delivery_method_data = None

        if has_personal_telegram_contact:
            personal_telegram_contact_data = UserContactInputFactory.build_json()
            await UserContact.create(
                user_id=proxy_auth_data.user_id,
                kind=UserContactKind.PERSONAL_TELEGRAM,
                **personal_telegram_contact_data,
            )
        else:
            personal_telegram_contact_data = None

    telegram_notification_settings: AnyJSON | None = (
        {
            "connection": delivery_method_data,
            "contact": personal_telegram_contact_data,
        }
        if has_telegram_delivery_method
        else None
    )

    assert_response(
        authorized_client.get(
            "/api/protected/notification-service/users/current/notification-settings/"
        ),
        expected_json={
            "telegram": telegram_notification_settings,
        },
    )

    async with active_session():
        await TelegramDeliveryMethod.delete_by_kwargs(user_id=proxy_auth_data.user_id)
        await UserContact.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=UserContactKind.PERSONAL_TELEGRAM,
        )
