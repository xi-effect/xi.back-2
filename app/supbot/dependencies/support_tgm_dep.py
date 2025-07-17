from typing import Any

from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext

from app.common.aiogram_ext import MessageExt
from app.supbot.models.support_db import SupportTicket


class SupportTicketFilter(Filter):
    async def __call__(  # noqa: FNE005
        self,
        message: MessageExt,
        state: FSMContext,
    ) -> bool | dict[str, Any]:
        if message.chat.type == "private":
            message_thread_id = (await state.get_data()).get("thread_id")
        elif message.chat.type == "supergroup":
            message_thread_id = message.message_thread_id
        else:  # pragma: no cover  # exclusive situations, maybe they could be covered
            return False

        ticket = await SupportTicket.find_first_by_id(message_thread_id)

        if ticket is None or ticket.closed:  # pragma: no cover
            return False

        return {"ticket": ticket}
