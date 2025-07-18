from aiogram import Router
from aiogram.filters import KICKED, ChatMemberUpdatedFilter, CommandStart

from app.common.aiogram_ext import (
    ChatMemberUpdatedExt,
    MessageExt,
    MessageFromUser,
    StartCommandWithDeepLinkObject,
)
from app.notifications import texts
from app.notifications.config import telegram_deep_link_provider
from app.notifications.dependencies.telegram_connections_tgm_dep import (
    TelegramConnectionFilter,
)
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)
from app.notifications.services import user_contacts_svc
from app.notifications.utils.deep_links import DeepLinkException

router = Router(name="telegram connections")


async def check_if_other_connections_exist_and_replace_them(chat_id: int) -> bool:
    telegram_connection = await TelegramConnection.find_first_by_chat_id_and_status(
        chat_id=chat_id,
        allowed_statuses=[
            TelegramConnectionStatus.ACTIVE,
            TelegramConnectionStatus.BLOCKED,
        ],
    )
    if telegram_connection is None:
        return False

    telegram_connection.status = TelegramConnectionStatus.REPLACED
    await user_contacts_svc.remove_personal_telegram_contact(
        user_id=telegram_connection.user_id
    )
    # TODO notify user on-platform (& email?) about the connection replacement
    return True


@router.message(CommandStart(deep_link=True))
async def create_telegram_connection(
    message: MessageFromUser,
    command: StartCommandWithDeepLinkObject,
) -> None:
    try:
        user_id = telegram_deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=command.args
        )
    except DeepLinkException:
        await message.answer(texts.INVALID_TOKEN_MESSAGE)
        return

    telegram_connection = await TelegramConnection.find_first_by_id(user_id)
    if telegram_connection is not None:
        await message.answer(
            texts.NOTIFICATIONS_ALREADY_CONNECTED_MESSAGE
            if telegram_connection.chat_id == message.chat.id
            else texts.TOKEN_ALREADY_USED_MESSAGE
        )
        return

    is_replacing_another_connection = (
        await check_if_other_connections_exist_and_replace_them(chat_id=message.chat.id)
    )

    await TelegramConnection.create(
        user_id=user_id,
        chat_id=message.chat.id,
        status=TelegramConnectionStatus.ACTIVE,
    )
    await user_contacts_svc.sync_personal_telegram_contact(
        user_id=user_id,
        new_username=message.from_user.username,
    )

    # TODO notify user on-platform (frontend?) about the connection completion

    await message.answer(
        texts.NOTIFICATIONS_REPLACES_MESSAGE
        if is_replacing_another_connection
        else texts.NOTIFICATIONS_CONNECTED_MESSAGE
    )


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=KICKED),
    TelegramConnectionFilter(TelegramConnectionStatus.ACTIVE),
)
async def block_telegram_connection(
    _event: ChatMemberUpdatedExt,
    telegram_connection: TelegramConnection,
) -> None:
    telegram_connection.status = TelegramConnectionStatus.BLOCKED
    await user_contacts_svc.remove_personal_telegram_contact(
        user_id=telegram_connection.user_id
    )
    # TODO notify user on-platform about the blocked connection


@router.message(
    CommandStart(),
    TelegramConnectionFilter(TelegramConnectionStatus.BLOCKED),
)
async def unblock_telegram_connection(
    message: MessageFromUser,
    telegram_connection: TelegramConnection,
) -> None:
    telegram_connection.status = TelegramConnectionStatus.ACTIVE
    await user_contacts_svc.sync_personal_telegram_contact(
        user_id=telegram_connection.user_id,
        new_username=message.from_user.username,
    )
    # TODO notify user on-platform (frontend?) about the unblocked connection
    await message.answer(texts.NOTIFICATIONS_RECONNECTED_MESSAGE)


@router.message(CommandStart())
async def start_without_deep_link(message: MessageExt) -> None:
    await message.answer(texts.START_WITHOUT_DEEP_LINK_MESSAGE)
