from aiogram import F
from aiogram.filters import Command, Filter, or_f

from app.supbot import texts


def command_filter(command: str) -> Filter:
    return or_f(
        Command(command),
        F.text == texts.COMMAND_DESCRIPTIONS[f"/{command}"],
    )
