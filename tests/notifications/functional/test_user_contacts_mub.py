import pytest
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.delivery_methods_db import DeliveryMethod
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services.user_contact_syncers.base_user_contact_syncer import (
    BaseUserContactSyncer,
)
from tests.common.assert_contains_ext import assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "delivery_method",
    [
        pytest.param(lf("active_telegram_delivery_method"), id="telegram"),
        pytest.param(lf("active_vk_delivery_method"), id="vk"),
    ],
)
@pytest.mark.parametrize(
    "has_username",
    [
        pytest.param(True, id="with_username"),
        pytest.param(False, id="no_username"),
    ],
)
async def test_syncing_messenger_user_contact(
    mock_stack: MockStack,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    user_contact: UserContact,
    user_contact_data: AnyJSON,
    delivery_method: DeliveryMethod,
    has_username: bool,
) -> None:
    # Specific cases are tested in service/user_contact_syncers/*
    sync_messenger_user_contact_mock = mock_stack.enter_async_mock(
        BaseUserContactSyncer,
        "sync_with_origin",
        return_value=user_contact if has_username else None,
    )

    assert_response(
        mub_client.post(
            "/mub/notification-service"
            f"/users/{proxy_auth_data.user_id}"
            f"/delivery-methods/{delivery_method.kind}"
            "/user-contact/sync-requests/",
        ),
        expected_json=user_contact_data if has_username else None,
    )

    sync_messenger_user_contact_mock.assert_awaited_once_with()


@pytest.mark.parametrize(
    "delivery_method",
    [
        pytest.param(lf("inactive_telegram_delivery_method"), id="telegram"),
        pytest.param(lf("inactive_vk_delivery_method"), id="vk"),
    ],
)
async def test_syncing_messenger_user_contact_delivery_method_not_active(
    mock_stack: MockStack,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    delivery_method: DeliveryMethod,
) -> None:
    sync_messenger_user_contact_mock = mock_stack.enter_async_mock(
        BaseUserContactSyncer,
        "sync_with_origin",
    )

    assert_response(
        mub_client.post(
            "/mub/notification-service"
            f"/users/{proxy_auth_data.user_id}"
            f"/delivery-methods/{delivery_method.kind}"
            "/user-contact/sync-requests/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Delivery method is not active"},
    )

    sync_messenger_user_contact_mock.assert_not_called()


@pytest.mark.parametrize(
    "delivery_method_kind",
    [
        pytest.param(DeliveryMethodKind.TELEGRAM, id="telegram"),
        pytest.param(DeliveryMethodKind.VK, id="vk"),
    ],
)
async def test_syncing_messenger_user_contact_delivery_method_not_found(
    mock_stack: MockStack,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    delivery_method_kind: DeliveryMethodKind,
) -> None:
    sync_messenger_user_contact_mock = mock_stack.enter_async_mock(
        BaseUserContactSyncer,
        "sync_with_origin",
    )

    assert_response(
        mub_client.post(
            "/mub/notification-service"
            f"/users/{proxy_auth_data.user_id}"
            f"/delivery-methods/{delivery_method_kind}"
            "/user-contact/sync-requests/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Delivery method not found"},
    )

    sync_messenger_user_contact_mock.assert_not_called()
