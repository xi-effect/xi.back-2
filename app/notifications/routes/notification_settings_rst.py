from app.common.fastapi_ext import APIRouterExt
from app.notifications.dependencies.notification_settings_dep import (
    MyNotificationSettings,
)
from app.notifications.models.notification_settings_db import NotificationSettings

router = APIRouterExt(tags=["notification settings"])


@router.get(
    path="/users/current/notification-settings/",
    response_model=NotificationSettings.ResponseSchema,
    summary="Retrieve current user's notification settings",
)
async def retrieve_notification_settings(
    notification_settings: MyNotificationSettings,
) -> NotificationSettings:
    return notification_settings


@router.patch(
    path="/users/current/notification-settings/",
    response_model=NotificationSettings.ResponseSchema,
    summary="Update current user's notification settings",
)
async def patch_notification_settings(
    notification_settings: MyNotificationSettings,
    data: NotificationSettings.PatchSchema,
) -> NotificationSettings:
    notification_settings.update(**data.model_dump(exclude_defaults=True))
    return notification_settings
