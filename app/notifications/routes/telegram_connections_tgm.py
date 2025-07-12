from aiogram import Router
from aiogram.filters import CommandObject, CommandStart

from app.common.aiogram_ext import MessageExt
from app.notifications import texts

router = Router(name="telegram connections")


@router.message(CommandStart(deep_link=True))
async def start(message: MessageExt, command: CommandObject) -> None:
    await message.answer(texts.WELCOME_MESSAGE)
    await message.answer(command.args or "")
