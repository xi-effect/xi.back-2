from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.notifications.dependencies.recipient_notifications_dep import (
    MyRecipientNotificationByID,
)
from app.notifications.models.notifications_db import (
    NotificationSearchRequestSchema,
)
from app.notifications.models.recipient_notifications_db import RecipientNotification

router = APIRouterExt(tags=["notifications"])


@router.post(
    path="/users/current/notifications/searches/",
    response_model=list[RecipientNotification.ResponseSchema],
    summary="List paginated notifications for the current user",
)
async def list_notifications(
    auth_data: AuthorizationData,
    data: NotificationSearchRequestSchema,
) -> Sequence[RecipientNotification]:
    return await RecipientNotification.find_paginated_by_recipient_user_id(
        recipient_user_id=auth_data.user_id,
        search_params=data,
    )


@router.get(
    path="/users/current/unread-notifications-count/",
    summary="Count unread notifications for the current user",
)
async def count_unread_notifications(
    auth_data: AuthorizationData,
    limit: Annotated[int, Query(gt=0, le=100)] = 100,
) -> int:
    return await RecipientNotification.count_unread_by_recipient_user_id(
        recipient_user_id=auth_data.user_id,
        limit=limit,
    )


class NotificationReadResponses(Responses):
    NOTIFICATION_ALREADY_MARKED_AS_READ = (
        status.HTTP_409_CONFLICT,
        "Notification already marked as read",
    )


@router.post(
    path="/users/current/notifications/{notification_id}/read/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NotificationReadResponses.responses(),
    summary="Mark a notification by id as read by the current user",
)
async def mark_notification_as_read(
    recipient_notification: MyRecipientNotificationByID,
) -> None:
    if recipient_notification.read_at is not None:
        raise NotificationReadResponses.NOTIFICATION_ALREADY_MARKED_AS_READ
    recipient_notification.mark_as_read()
