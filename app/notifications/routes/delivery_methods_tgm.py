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
from app.notifications.dependencies.delivery_methods_tgm_dep import (
    TelegramDeliveryMethodFilter,
)
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    TelegramDeliveryMethod,
)
from app.notifications.services.user_contact_syncers.telegram_user_contact_syncer import (
    TelegramUserContactSyncer,
)
from app.notifications.utils.deep_links import DeepLinkException

router = Router(name="delivery methods")


@router.message(CommandStart(deep_link=True))
async def create_telegram_delivery_method(
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

    peer_id: int = message.chat.id

    delivery_method = await TelegramDeliveryMethod.find_first_by_user_id(
        user_id=user_id
    )
    if delivery_method is not None:
        await message.answer(
            texts.NOTIFICATIONS_ALREADY_CONNECTED_MESSAGE
            if delivery_method.peer_id == peer_id
            else texts.TOKEN_ALREADY_USED_MESSAGE
        )
        return

    delivery_method_to_replace = (
        await TelegramDeliveryMethod.find_first_by_peer_id_and_status(
            peer_id=peer_id,
            allowed_statuses=[
                DeliveryMethodStatus.ACTIVE,
                DeliveryMethodStatus.BLOCKED,
            ],
        )
    )
    if delivery_method_to_replace is None:
        is_replacing_another_connection = False
    else:
        delivery_method_to_replace.status = DeliveryMethodStatus.REPLACED
        await TelegramUserContactSyncer(
            delivery_method=delivery_method_to_replace
        ).remove()
        # TODO notify user on-platform (& email?) about the connection replacement
        is_replacing_another_connection = True

    delivery_method = await TelegramDeliveryMethod.create(
        user_id=user_id,
        peer_id=peer_id,
        status=DeliveryMethodStatus.ACTIVE,
    )
    await TelegramUserContactSyncer(delivery_method=delivery_method).sync_from_message(
        message=message
    )

    # TODO notify user on-platform (frontend?) about the connection completion
    await message.answer(
        texts.NOTIFICATIONS_REPLACES_MESSAGE
        if is_replacing_another_connection
        else texts.NOTIFICATIONS_CONNECTED_MESSAGE
    )


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=KICKED),
    TelegramDeliveryMethodFilter(DeliveryMethodStatus.ACTIVE),
)
async def block_telegram_delivery_method(
    _event: ChatMemberUpdatedExt,
    delivery_method: TelegramDeliveryMethod,
) -> None:
    delivery_method.status = DeliveryMethodStatus.BLOCKED
    await TelegramUserContactSyncer(delivery_method=delivery_method).remove()
    # TODO notify user on-platform about the blocked connection


@router.message(
    CommandStart(),
    TelegramDeliveryMethodFilter(DeliveryMethodStatus.BLOCKED),
)
async def unblock_telegram_delivery_method(
    message: MessageFromUser,
    delivery_method: TelegramDeliveryMethod,
) -> None:
    delivery_method.status = DeliveryMethodStatus.ACTIVE
    await TelegramUserContactSyncer(delivery_method=delivery_method).sync_from_message(
        message=message
    )
    # TODO notify user on-platform (frontend?) about the unblocked connection
    await message.answer(texts.NOTIFICATIONS_RECONNECTED_MESSAGE)


@router.message(CommandStart())
async def start_without_deep_link(message: MessageExt) -> None:
    await message.answer(texts.START_WITHOUT_DEEP_LINK_MESSAGE)
