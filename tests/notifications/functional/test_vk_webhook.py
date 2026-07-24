from typing import Any

import pytest
from faker import Faker
from httpx import Response
from pydantic_marshals.contains import assert_contains
from respx import MockRouter, Route
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.notifications import texts
from app.notifications.config import vk_connection_key_provider
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    VKDeliveryMethod,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.id_provider import IDProvider
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.notifications import factories

pytestmark = pytest.mark.anyio


def assert_vk_webhook_response(
    response: Response,
    expected_text: str = "ok",
) -> None:
    assert_contains(
        {
            "status_code": response.status_code,
            "headers": response.headers,
            "text": response.text,
        },
        {
            "status_code": status.HTTP_200_OK,
            "headers": {"Content-Type": "text/plain; charset=utf-8"},
            "text": expected_text,
        },
    )


def assert_vk_message_sent(
    vk_send_message_mock: Route,
    expected_peer_id: int,
    expected_message: str,
) -> None:
    assert_last_httpx_request(
        vk_send_message_mock,
        expected_data={
            "peer_id": [str(expected_peer_id)],
            "message": [expected_message],
        },
    )


async def test_handling_update_from_vk_confirmation(
    client: TestClient,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_confirmation_code: str,
    vk_notifications_bot_webhook_secret_key: str,
) -> None:
    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.ConfirmationUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key
            ),
        ),
        expected_text=vk_notifications_bot_confirmation_code,
    )


@pytest.mark.parametrize(
    ("other_delivery_method_status", "expected_reply_text"),
    [
        pytest.param(
            None,
            texts.NOTIFICATIONS_CONNECTED_MESSAGE,
            id="no_other_delivery_methods",
        ),
        pytest.param(
            DeliveryMethodStatus.REPLACED,
            texts.NOTIFICATIONS_CONNECTED_MESSAGE,
            id="existing_replaced_delivery_method",
        ),
        pytest.param(
            DeliveryMethodStatus.ACTIVE,
            texts.NOTIFICATIONS_REPLACES_MESSAGE,
            id="existing_active_delivery_method",
        ),
        pytest.param(
            DeliveryMethodStatus.BLOCKED,
            texts.NOTIFICATIONS_REPLACES_MESSAGE,
            id="existing_blocked_delivery_method",
        ),
    ],
)
async def test_handling_update_from_vk_allow_messages_delivery_method_creating(
    active_session: ActiveSession,
    id_provider: IDProvider,
    client: TestClient,
    authorized_user_id: int,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_peer_id: int,
    vk_send_message_mock: Route,
    other_delivery_method_status: DeliveryMethodStatus | None,
    expected_reply_text: str,
) -> None:
    other_user_id: int = id_provider.generate_id()
    if other_delivery_method_status is not None:
        async with active_session():
            other_delivery_method = await VKDeliveryMethod.create(
                user_id=other_user_id,
                peer_id=vk_peer_id,
                status=other_delivery_method_status,
            )

    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.AllowMessagesUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key,
                object=factories.AllowMessagesObjectFactory.build(
                    user_id=vk_peer_id,
                    key=vk_connection_key_provider.create_signed_link_payload(
                        user_id=authorized_user_id
                    ),
                ),
            ),
        )
    )

    assert_vk_message_sent(
        vk_send_message_mock,
        expected_peer_id=vk_peer_id,
        expected_message=expected_reply_text,
    )

    async with active_session() as session:
        delivery_method = await VKDeliveryMethod.find_first_by_user_id(
            user_id=authorized_user_id
        )
        assert delivery_method is not None
        assert_contains(
            delivery_method,
            {
                "peer_id": vk_peer_id,
                "status": DeliveryMethodStatus.ACTIVE,
            },
        )
        await delivery_method.delete()

        if other_delivery_method_status is not None:
            session.add(other_delivery_method)
            await session.refresh(other_delivery_method)
            assert other_delivery_method.status is DeliveryMethodStatus.REPLACED
            await other_delivery_method.delete()


async def test_handling_update_from_vk_allow_messages_delivery_method_already_exists(
    active_session: ActiveSession,
    id_provider: IDProvider,
    client: TestClient,
    authorized_user_id: int,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_peer_id: int,
    vk_send_message_mock: Route,
) -> None:
    async with active_session():
        await VKDeliveryMethod.create(
            user_id=authorized_user_id,
            peer_id=id_provider.generate_id(),
            status=DeliveryMethodStatus.ACTIVE,
        )

    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.AllowMessagesUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key,
                object=factories.AllowMessagesObjectFactory.build(
                    user_id=vk_peer_id,
                    key=vk_connection_key_provider.create_signed_link_payload(
                        user_id=authorized_user_id
                    ),
                ),
            ),
        )
    )

    assert_vk_message_sent(
        vk_send_message_mock,
        expected_peer_id=vk_peer_id,
        expected_message=texts.TOKEN_ALREADY_USED_MESSAGE,
    )

    async with active_session():
        await VKDeliveryMethod.delete_by_kwargs(user_id=authorized_user_id)


async def test_handling_update_from_vk_allow_messages_invalid_connection_key(
    faker: Faker,
    client: TestClient,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_peer_id: int,
    vk_send_message_mock: Route,
) -> None:
    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.AllowMessagesUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key,
                object=factories.AllowMessagesObjectFactory.build(
                    user_id=vk_peer_id,
                    key=faker.pystr(),
                ),
            ),
        )
    )

    assert_vk_message_sent(
        vk_send_message_mock,
        expected_peer_id=vk_peer_id,
        expected_message=texts.INVALID_TOKEN_MESSAGE,
    )


@pytest.mark.parametrize(
    "is_connection_key_used",
    [
        pytest.param(True, id="with_connection_key"),
        pytest.param(False, id="no_connection_key"),
    ],
)
async def test_handling_update_from_vk_allow_messages_delivery_method_reactivating(
    active_session: ActiveSession,
    client: TestClient,
    authorized_user_id: int,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_peer_id: int,
    vk_send_message_mock: Route,
    is_connection_key_used: bool,
) -> None:
    async with active_session():
        delivery_method = await VKDeliveryMethod.create(
            user_id=authorized_user_id,
            peer_id=vk_peer_id,
            status=DeliveryMethodStatus.BLOCKED,
        )

    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.AllowMessagesUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key,
                object=factories.AllowMessagesObjectFactory.build(
                    user_id=vk_peer_id,
                    key=(
                        vk_connection_key_provider.create_signed_link_payload(
                            user_id=authorized_user_id
                        )
                        if is_connection_key_used
                        else ""
                    ),
                ),
            ),
        )
    )

    assert_vk_message_sent(
        vk_send_message_mock,
        expected_peer_id=vk_peer_id,
        expected_message=texts.NOTIFICATIONS_RECONNECTED_MESSAGE,
    )

    async with active_session() as session:
        session.add(delivery_method)
        await session.refresh(delivery_method)
        assert delivery_method.status is DeliveryMethodStatus.ACTIVE
        await delivery_method.delete()


@pytest.mark.parametrize(
    "is_connection_key_used",
    [
        pytest.param(True, id="with_connection_key"),
        pytest.param(False, id="no_connection_key"),
    ],
)
async def test_handling_update_from_vk_allow_messages_delivery_method_is_already_active(
    active_session: ActiveSession,
    vk_respx_mock: MockRouter,
    client: TestClient,
    authorized_user_id: int,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_peer_id: int,
    is_connection_key_used: bool,
) -> None:
    async with active_session():
        delivery_method = await VKDeliveryMethod.create(
            user_id=authorized_user_id,
            peer_id=vk_peer_id,
            status=DeliveryMethodStatus.ACTIVE,
        )

    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.AllowMessagesUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key,
                object=factories.AllowMessagesObjectFactory.build(
                    user_id=vk_peer_id,
                    key=(
                        vk_connection_key_provider.create_signed_link_payload(
                            user_id=authorized_user_id
                        )
                        if is_connection_key_used
                        else ""
                    ),
                ),
            ),
        )
    )

    assert vk_respx_mock.calls.call_count == 0

    async with active_session() as session:
        session.add(delivery_method)
        await session.refresh(delivery_method)
        assert delivery_method.status is DeliveryMethodStatus.ACTIVE
        await delivery_method.delete()


async def test_handling_update_from_vk_allow_messages_delivery_method_not_found(
    client: TestClient,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_peer_id: int,
    vk_send_message_mock: Route,
) -> None:
    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.AllowMessagesUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key,
                object=factories.AllowMessagesObjectFactory.build(
                    user_id=vk_peer_id,
                    key="",
                ),
            ),
        )
    )

    assert_vk_message_sent(
        vk_send_message_mock,
        expected_peer_id=vk_peer_id,
        expected_message=texts.START_WITHOUT_DEEP_LINK_MESSAGE,
    )


async def test_handling_update_from_vk_deny_messages_delivery_method_blocking(
    active_session: ActiveSession,
    client: TestClient,
    authorized_user_id: int,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_peer_id: int,
) -> None:
    async with active_session():
        delivery_method = await VKDeliveryMethod.create(
            user_id=authorized_user_id,
            peer_id=vk_peer_id,
            status=DeliveryMethodStatus.ACTIVE,
        )

    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.DenyMessagesUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key,
                object=factories.DenyMessagesObjectFactory.build(user_id=vk_peer_id),
            ),
        )
    )

    async with active_session() as session:
        session.add(delivery_method)
        await session.refresh(delivery_method)
        assert delivery_method.status is DeliveryMethodStatus.BLOCKED
        await delivery_method.delete()


@pytest.mark.parametrize(
    "delivery_method_status",
    [
        pytest.param(None, id="no_delivery_method"),
        *(
            pytest.param(
                delivery_method_status,
                id=f"{delivery_method_status.value}_delivery_method",
            )
            for delivery_method_status in DeliveryMethodStatus
            if delivery_method_status is not DeliveryMethodStatus.ACTIVE
        ),
    ],
)
async def test_handling_update_from_vk_deny_messages_delivery_method_is_not_active(
    active_session: ActiveSession,
    client: TestClient,
    authorized_user_id: int,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_peer_id: int,
    delivery_method_status: DeliveryMethodStatus | None,
) -> None:
    if delivery_method_status is not None:
        async with active_session():
            await VKDeliveryMethod.create(
                user_id=authorized_user_id,
                peer_id=vk_peer_id,
                status=delivery_method_status,
            )

    assert_vk_webhook_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=factories.DenyMessagesUpdateFactory.build_json(
                secret=vk_notifications_bot_webhook_secret_key,
                object=factories.DenyMessagesObjectFactory.build(user_id=vk_peer_id),
            ),
        )
    )

    async with active_session():
        delivery_method = await VKDeliveryMethod.find_first_by_user_id(
            user_id=authorized_user_id
        )
        if delivery_method_status is None:
            assert delivery_method is None
        else:
            assert delivery_method is not None
            assert delivery_method.status is delivery_method_status
            await delivery_method.delete()


@pytest.mark.parametrize(
    "vk_update_factory",
    [
        pytest.param(factories.ConfirmationUpdateFactory, id="confirmation"),
        pytest.param(factories.AllowMessagesUpdateFactory, id="allow_messages"),
        pytest.param(factories.DenyMessagesUpdateFactory, id="deny_messages"),
    ],
)
async def test_handling_update_from_vk_missing_configuration(
    mock_stack: MockStack,
    client: TestClient,
    vk_notifications_bot_webhook_url: str,
    vk_notifications_bot_webhook_secret_key: str,
    vk_update_factory: type[BaseModelFactory[Any]],
) -> None:
    mock_stack.enter_patch(settings, "vk_notifications_bot", new=None)

    assert_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=vk_update_factory.build_json(
                secret=vk_notifications_bot_webhook_secret_key
            ),
        ),
        expected_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        expected_json={"detail": "Notifications bot configuration is missing"},
    )


@pytest.mark.parametrize(
    "is_secret_passed",
    [
        pytest.param(False, id="missing_token"),
        pytest.param(True, id="invalid_token"),
    ],
)
@pytest.mark.parametrize(
    "vk_update_factory",
    [
        pytest.param(factories.ConfirmationUpdateFactory, id="confirmation"),
        pytest.param(factories.AllowMessagesUpdateFactory, id="allow_messages"),
        pytest.param(factories.DenyMessagesUpdateFactory, id="deny_messages"),
    ],
)
async def test_handling_update_from_vk_invalid_webhook_token(
    faker: Faker,
    client: TestClient,
    vk_notifications_bot_webhook_url: str,
    vk_update_factory: type[BaseModelFactory[Any]],
    is_secret_passed: bool,
) -> None:
    assert_response(
        client.post(
            vk_notifications_bot_webhook_url,
            json=vk_update_factory.build_json(
                secret=faker.pystr() if is_secret_passed else None
            ),
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Invalid webhook token"},
    )
