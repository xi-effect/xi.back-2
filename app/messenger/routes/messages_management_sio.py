from tmexio import Emitter, EventException

from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.messenger.dependencies.messages_sio_dep import MessageByIds
from app.messenger.models.messages_db import MessageIdsSchema
from app.messenger.rooms import chat_room

router = EventRouterExt(tags=["managing-messages"])

message_already_pinned = EventException(409, "Message is already pinned")


@router.on(
    "pin-chat-message",
    summary="Pin any chat message by id",
    server_summary="Chat message in the current chat has been pinned",
    exceptions=[message_already_pinned],
    # TODO dependencies=[allowed_pinning_dependency],
)
async def pin_message(
    message: MessageByIds,
    duplex_emitter: Emitter[MessageIdsSchema],
) -> None:
    if message.pinned:
        raise message_already_pinned

    message.pinned = True
    await db.session.commit()

    await duplex_emitter.emit(
        MessageIdsSchema(chat_id=message.chat_id, message_id=message.id),
        target=chat_room(message.chat_id),
        exclude_self=True,
    )


message_not_pinned = EventException(409, "Message is not pinned")


@router.on(
    "unpin-chat-message",
    summary="Unpin any chat message by id",
    server_summary="Chat message in the current chat has been unpinned",
    exceptions=[message_not_pinned],
    # TODO dependencies=[allowed_pinning_dependency],
)
async def unpin_message(
    message: MessageByIds,
    duplex_emitter: Emitter[MessageIdsSchema],
) -> None:
    if not message.pinned:
        raise message_not_pinned

    message.pinned = False
    await db.session.commit()

    await duplex_emitter.emit(
        MessageIdsSchema(chat_id=message.chat_id, message_id=message.id),
        target=chat_room(message.chat_id),
        exclude_self=True,
    )
