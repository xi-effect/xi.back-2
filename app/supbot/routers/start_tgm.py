from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import ReplyKeyboardMarkup

from app.common.aiogram_ext import MessageExt
from app.supbot import texts

router = Router(name="start")


@router.message(StateFilter(None), CommandStart())
async def start_bot(message: MessageExt) -> None:
    await message.answer(
        texts.WELCOME_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=texts.MAIN_MENU_KEYBOARD_MARKUP, resize_keyboard=True
        ),
    )
