from aiogram import Router
from aiogram.filters import CommandStart

from app.common.aiogram_ext import (
    MessageExt,
    StartCommandWithDeepLinkObject,
)
from app.notifications import texts
from app.notifications.config import telegram_deep_link_provider
from app.notifications.utils.deep_links import DeepLinkException

router = Router(name="telegram connections")


@router.message(CommandStart(deep_link=True))
async def start_with_deep_link(
    message: MessageExt,
    command: StartCommandWithDeepLinkObject,
) -> None:
    try:
        user_id = telegram_deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=command.args
        )
    except DeepLinkException:
        await message.answer(texts.INVALID_TOKEN_MESSAGE)
        return

    await message.answer(texts.WELCOME_MESSAGE)
    await message.answer(str(user_id))
