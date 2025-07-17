from pydantic import BaseModel, ConfigDict

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.notifications.models.telegram_connections_db import TelegramConnection
from app.notifications.models.user_contacts_db import ContactKind, UserContact

router = APIRouterExt(tags=["notification settings"])


# Using pre-schemas because of a bug in `CompositeMarshalModel`
# https://github.com/niqzart/pydantic-marshals/issues/38


class TelegramNotificationSettingsPreSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    connection: TelegramConnection
    contact: UserContact | None
    # TODO enabled_categories / _kinds


class NotificationSettingsPreSchema(BaseModel):
    # TODO email (enabled_categories / _kinds only)
    telegram: TelegramNotificationSettingsPreSchema | None
    # TODO vk


class TelegramNotificationSettingsSchema(BaseModel):
    connection: TelegramConnection.StatusSchema
    contact: UserContact.ResponseSchema | None


class NotificationSettingsSchema(BaseModel):
    telegram: TelegramNotificationSettingsSchema | None


@router.get(
    path="/users/current/notification-settings/",
    response_model=NotificationSettingsSchema,
    summary="Retrieve notification settings for the current user",
)
async def retrieve_notification_settings(
    auth_data: AuthorizationData,
) -> NotificationSettingsPreSchema:
    telegram_connection = await TelegramConnection.find_first_by_id(auth_data.user_id)
    return NotificationSettingsPreSchema(
        telegram=(
            None
            if telegram_connection is None
            else TelegramNotificationSettingsPreSchema(
                connection=telegram_connection,
                contact=await UserContact.find_first_by_primary_key(
                    user_id=auth_data.user_id,
                    kind=ContactKind.PERSONAL_TELEGRAM,
                ),
            )
        ),
    )
