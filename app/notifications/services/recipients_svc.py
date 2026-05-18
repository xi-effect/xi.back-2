from collections.abc import AsyncIterator
from typing import assert_never

from app.common.config_bdg import classrooms_bridge
from app.common.schemas.notifications_sch import (
    AnyRecipientFilterSchema,
    ClassroomParticipantRecipientFilterSchema,
    NotificationInputSchema,
    NotificationInputV2Schema,
    SingleUserRecipientFilterSchema,
)


async def iter_recipient_user_ids_from_filter(
    recipient_filter: AnyRecipientFilterSchema,
) -> AsyncIterator[int]:
    match recipient_filter:
        case SingleUserRecipientFilterSchema():
            yield recipient_filter.user_id
        case ClassroomParticipantRecipientFilterSchema():
            for (
                recipient_user_id
            ) in await classrooms_bridge.list_classroom_participant_ids(
                classroom_id=recipient_filter.classroom_id,
                role=recipient_filter.role,
            ):
                yield recipient_user_id
        case _:
            assert_never(recipient_filter)


async def generate_recipient_user_ids_for_notification(
    notification_data: NotificationInputSchema | NotificationInputV2Schema,
) -> list[int]:
    match notification_data:
        case NotificationInputSchema():
            return list(set(notification_data.recipient_user_ids))
        case NotificationInputV2Schema():
            return list(
                {
                    user_id
                    for recipient_filter in notification_data.recipient_filters
                    async for user_id in iter_recipient_user_ids_from_filter(
                        recipient_filter=recipient_filter,
                    )
                }
            )
        case _:
            assert_never(notification_data)
