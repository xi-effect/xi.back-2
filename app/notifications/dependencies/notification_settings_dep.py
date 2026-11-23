from typing import Annotated

from fastapi import Depends

from app.common.dependencies.authorization_dep import AuthorizationData
from app.notifications.models.notification_settings_db import NotificationSettings


async def get_my_notification_settings(
    auth_data: AuthorizationData,
) -> NotificationSettings:
    notification_settings = await NotificationSettings.find_first_by_id(
        auth_data.user_id
    )
    if notification_settings is None:
        return await NotificationSettings.create(user_id=auth_data.user_id)
    return notification_settings


MyNotificationSettings = Annotated[
    NotificationSettings, Depends(get_my_notification_settings)
]
