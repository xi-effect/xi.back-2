import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services import telegram_connections_svc, user_contacts_svc
from tests.common.assert_contains_ext import assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "has_username_in_telegram",
    [
        pytest.param(True, id="with_username_in_telegram"),
        pytest.param(False, id="no_username_in_telegram"),
    ],
)
async def test_personal_telegram_contact_syncing(
    faker: Faker,
    mock_stack: MockStack,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    user_contact: UserContact,
    user_contact_data: AnyJSON,
    has_username_in_telegram: bool,
) -> None:
    new_username = faker.user_name() if has_username_in_telegram else None
    # Specific cases for telegram_connections_svc are tested in service/test_telegram_connections_svc
    retrieve_telegram_username_by_user_id_mock = mock_stack.enter_async_mock(
        telegram_connections_svc,
        "retrieve_telegram_username_by_user_id",
        return_value=new_username,
    )
    # Specific cases for user_contacts_svc are tested in service/test_user_contacts_svc
    sync_personal_telegram_contact_mock = mock_stack.enter_async_mock(
        user_contacts_svc,
        "sync_personal_telegram_contact",
        return_value=user_contact if has_username_in_telegram else None,
    )

    assert_response(
        mub_client.post(
            f"/mub/notification-service/users/{proxy_auth_data.user_id}/contacts/personal-telegram/sync-requests/",
        ),
        expected_json=user_contact_data if has_username_in_telegram else None,
    )

    retrieve_telegram_username_by_user_id_mock.assert_awaited_once_with(
        user_id=proxy_auth_data.user_id,
    )
    sync_personal_telegram_contact_mock.assert_awaited_once_with(
        user_id=proxy_auth_data.user_id,
        new_username=new_username,
    )
