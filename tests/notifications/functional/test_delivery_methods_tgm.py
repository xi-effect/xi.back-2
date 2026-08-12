import random
from datetime import datetime

import pytest
from aiogram.enums import ChatMemberStatus
from aiogram.methods import SendMessage
from aiogram.types import Chat, ChatMemberBanned, ChatMemberMember
from faker import Faker
from pydantic_marshals.contains import assert_contains

from app.notifications import texts
from app.notifications.config import telegram_deep_link_provider
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    TelegramDeliveryMethod,
)
from app.notifications.services import user_contacts_svc
from tests.common.active_session import ActiveSession
from tests.common.aiogram_factories import (
    ChatMemberUpdatedFactory,
    MessageFactory,
    UpdateFactory,
    UserFactory,
)
from tests.common.aiogram_testing import MockedBot, TelegramBotWebhookDriver
from tests.common.id_provider import IDProvider
from tests.common.mock_stack import MockStack

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("other_delivery_method_status", "is_user_contact_removed", "expected_reply_text"),
    [
        pytest.param(
            None,
            False,
            texts.NOTIFICATIONS_CONNECTED_MESSAGE,
            id="no_other_delivery_methods",
        ),
        pytest.param(
            DeliveryMethodStatus.REPLACED,
            False,
            texts.NOTIFICATIONS_CONNECTED_MESSAGE,
            id="existing_replaces_delivery_method",
        ),
        pytest.param(
            DeliveryMethodStatus.ACTIVE,
            True,
            texts.NOTIFICATIONS_REPLACES_MESSAGE,
            id="existing_active_delivery_method",
        ),
        pytest.param(
            DeliveryMethodStatus.BLOCKED,
            True,
            texts.NOTIFICATIONS_REPLACES_MESSAGE,
            id="existing_blocked_delivery_method",
        ),
    ],
)
async def test_telegram_delivery_method_creating(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    id_provider: IDProvider,
    authorized_user_id: int,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
    other_delivery_method_status: DeliveryMethodStatus | None,
    is_user_contact_removed: bool,
    expected_reply_text: str,
) -> None:
    other_user_id = id_provider.generate_id()
    if other_delivery_method_status is not None:
        async with active_session():
            other_delivery_method = await TelegramDeliveryMethod.create(
                user_id=other_user_id,
                peer_id=tg_chat_id,
                status=other_delivery_method_status,
            )

    signed_deep_link_content = telegram_deep_link_provider.create_signed_link_payload(
        user_id=authorized_user_id
    )

    # Specific cases for user_contacts_svc are tested in service/test_user_contacts_svc
    sync_personal_telegram_contact_mock = mock_stack.enter_async_mock(
        user_contacts_svc, "sync_personal_telegram_contact"
    )
    remove_personal_telegram_contact_mock = mock_stack.enter_async_mock(
        user_contacts_svc, "remove_personal_telegram_contact"
    )

    new_username: str = faker.user_name()
    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=f"/start {signed_deep_link_content}",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id, username=new_username),
            ),
        )
    )

    sync_personal_telegram_contact_mock.assert_awaited_once_with(
        user_id=authorized_user_id,
        new_username=new_username,
    )
    if is_user_contact_removed:
        remove_personal_telegram_contact_mock.assert_awaited_once_with(
            user_id=other_user_id
        )
    else:
        remove_personal_telegram_contact_mock.assert_not_called()

    async with active_session() as session:
        delivery_method = await TelegramDeliveryMethod.find_first_by_user_id(
            user_id=authorized_user_id
        )
        assert delivery_method is not None
        assert_contains(
            delivery_method,
            {
                "peer_id": tg_chat_id,
                "status": DeliveryMethodStatus.ACTIVE,
            },
        )
        await delivery_method.delete()

        if other_delivery_method_status is not None:
            session.add(other_delivery_method)
            await session.refresh(other_delivery_method)
            assert other_delivery_method.status is DeliveryMethodStatus.REPLACED
            await other_delivery_method.delete()

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": expected_reply_text,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.parametrize(
    ("has_same_chat_id", "expected_reply_text"),
    [
        pytest.param(
            True,
            texts.NOTIFICATIONS_ALREADY_CONNECTED_MESSAGE,
            id="same_chat",
        ),
        pytest.param(
            False,
            texts.TOKEN_ALREADY_USED_MESSAGE,
            id="different_chat",
        ),
    ],
)
async def test_telegram_delivery_method_creating_delivery_method_already_exists(
    active_session: ActiveSession,
    id_provider: IDProvider,
    authorized_user_id: int,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
    has_same_chat_id: bool,
    expected_reply_text: str,
) -> None:
    async with active_session():
        await TelegramDeliveryMethod.create(
            user_id=authorized_user_id,
            peer_id=tg_chat_id if has_same_chat_id else id_provider.generate_id(),
            status=random.choice(list(DeliveryMethodStatus)),
        )

    signed_deep_link_content = telegram_deep_link_provider.create_signed_link_payload(
        user_id=authorized_user_id
    )

    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=f"/start {signed_deep_link_content}",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    async with active_session():
        await TelegramDeliveryMethod.delete_by_kwargs(user_id=authorized_user_id)

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": expected_reply_text,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_telegram_delivery_method_creating_invalid_token(
    faker: Faker,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    # Basic case to verify error handling. Specific cases are tested in unit/test_deep_links

    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=f"/start {faker.pystr()}",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.INVALID_TOKEN_MESSAGE,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_telegram_delivery_method_blocking(
    active_session: ActiveSession,
    authorized_user_id: int,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    bot_id: int,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    async with active_session():
        delivery_method = await TelegramDeliveryMethod.create(
            user_id=authorized_user_id,
            peer_id=tg_chat_id,
            status=DeliveryMethodStatus.ACTIVE,
        )

    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            my_chat_member=ChatMemberUpdatedFactory.build(
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
                old_chat_member=ChatMemberMember(
                    user=UserFactory.build(id=bot_id),
                    status=ChatMemberStatus.MEMBER,
                ),
                new_chat_member=ChatMemberBanned(
                    user=UserFactory.build(id=bot_id),
                    status=ChatMemberStatus.KICKED,
                    until_date=datetime.fromtimestamp(0),
                ),
            ),
        )
    )

    async with active_session() as session:
        session.add(delivery_method)
        await session.refresh(delivery_method)
        assert delivery_method.status is DeliveryMethodStatus.BLOCKED
        await delivery_method.delete()

    mocked_bot.assert_no_more_api_calls()


@pytest.mark.parametrize(
    "delivery_method_status",
    [
        pytest.param(None, id="no_delivery_method"),
        *(
            pytest.param(status, id=f"{status.value}_delivery_method")
            for status in DeliveryMethodStatus
            if status is not DeliveryMethodStatus.ACTIVE
        ),
    ],
)
async def test_telegram_delivery_method_blocking_delivery_method_is_not_active(
    active_session: ActiveSession,
    authorized_user_id: int,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    bot_id: int,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
    delivery_method_status: DeliveryMethodStatus | None,
) -> None:
    if delivery_method_status is not None:
        async with active_session():
            await TelegramDeliveryMethod.create(
                user_id=authorized_user_id,
                peer_id=tg_chat_id,
                status=delivery_method_status,
            )

    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            my_chat_member=ChatMemberUpdatedFactory.build(
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
                old_chat_member=ChatMemberMember(
                    user=UserFactory.build(id=bot_id),
                    status=ChatMemberStatus.MEMBER,
                ),
                new_chat_member=ChatMemberBanned(
                    user=UserFactory.build(id=bot_id),
                    status=ChatMemberStatus.KICKED,
                    until_date=datetime.fromtimestamp(0),
                ),
            ),
        )
    )

    async with active_session():
        delivery_method = await TelegramDeliveryMethod.find_first_by_user_id(
            user_id=authorized_user_id
        )
        if delivery_method_status is None:
            assert delivery_method is None
        else:
            assert delivery_method is not None
            assert delivery_method.status is delivery_method_status
            await delivery_method.delete()

    mocked_bot.assert_no_more_api_calls()


async def test_telegram_delivery_method_unblocking(
    active_session: ActiveSession,
    authorized_user_id: int,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    bot_id: int,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    async with active_session():
        delivery_method = await TelegramDeliveryMethod.create(
            user_id=authorized_user_id,
            peer_id=tg_chat_id,
            status=DeliveryMethodStatus.BLOCKED,
        )

    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text="/start",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    async with active_session() as session:
        session.add(delivery_method)
        await session.refresh(delivery_method)
        assert delivery_method.status is DeliveryMethodStatus.ACTIVE
        await delivery_method.delete()

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.NOTIFICATIONS_RECONNECTED_MESSAGE,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.parametrize(
    "delivery_method_status",
    [
        pytest.param(None, id="no_delivery_method"),
        *(
            pytest.param(status, id=f"{status.value}_delivery_method")
            for status in DeliveryMethodStatus
            if status is not DeliveryMethodStatus.BLOCKED
        ),
    ],
)
async def test_starting_without_deep_link(
    active_session: ActiveSession,
    authorized_user_id: int,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
    delivery_method_status: DeliveryMethodStatus | None,
) -> None:
    if delivery_method_status is not None:
        async with active_session():
            await TelegramDeliveryMethod.create(
                user_id=authorized_user_id,
                peer_id=tg_chat_id,
                status=delivery_method_status,
            )

    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text="/start",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    async with active_session():
        delivery_method = await TelegramDeliveryMethod.find_first_by_user_id(
            user_id=authorized_user_id
        )
        if delivery_method_status is None:
            assert delivery_method is None
        else:
            assert delivery_method is not None
            assert delivery_method.status is delivery_method_status
            await delivery_method.delete()

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.START_WITHOUT_DEEP_LINK_MESSAGE,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()
