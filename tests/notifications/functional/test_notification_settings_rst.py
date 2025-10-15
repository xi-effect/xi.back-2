import pytest
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)
from app.notifications.models.user_contacts_db import UserContact
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.notifications.factories import UserContactInputFactory

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("has_telegram_connection", "has_personal_telegram_contact"),
    [
        pytest.param(False, False, id="no_telegram"),
        pytest.param(True, False, id="with_telegram_connection-no_telegram_contact"),
        pytest.param(True, True, id="with_telegram_connection-with_telegram_contact"),
    ],
)
async def test_retrieving_notification_settings(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    tg_chat_id: int,
    random_telegram_connection_status: TelegramConnectionStatus,
    has_telegram_connection: bool,
    has_personal_telegram_contact: bool,
) -> None:
    async with active_session():
        if has_telegram_connection:
            telegram_connection_data = {"status": random_telegram_connection_status}
            await TelegramConnection.create(
                user_id=proxy_auth_data.user_id,
                chat_id=tg_chat_id,
                **telegram_connection_data,
            )
        else:
            telegram_connection_data = None

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
            "connection": telegram_connection_data,
            "contact": personal_telegram_contact_data,
        }
        if has_telegram_connection
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
        await TelegramConnection.delete_by_kwargs(user_id=proxy_auth_data.user_id)
        await UserContact.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=UserContactKind.PERSONAL_TELEGRAM,
        )
