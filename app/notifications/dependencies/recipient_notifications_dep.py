from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.notifications.models.recipient_notifications_db import RecipientNotification


class RecipientNotificationResponses(Responses):
    RECIPIENT_NOTIFICATION_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "Recipient notification not found",
    )


@with_responses(RecipientNotificationResponses)
async def get_my_recipient_notification_by_id(
    notification_id: UUID, auth_data: AuthorizationData
) -> RecipientNotification:
    recipient_notification = await RecipientNotification.find_first_by_ids(
        notification_id=notification_id,
        recipient_user_id=auth_data.user_id,
    )
    if recipient_notification is None:
        raise RecipientNotificationResponses.RECIPIENT_NOTIFICATION_NOT_FOUND
    return recipient_notification


MyRecipientNotificationByID = Annotated[
    RecipientNotification, Depends(get_my_recipient_notification_by_id)
]
