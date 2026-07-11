from pydantic import BaseModel, ConfigDict

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.models.delivery_methods_db import TelegramDeliveryMethod
from app.notifications.models.user_contacts_db import UserContact

router = APIRouterExt(tags=["notification settings"])


# Using pre-schemas because of a bug in `CompositeMarshalModel`
# https://github.com/niqzart/pydantic-marshals/issues/38


class TelegramNotificationSettingsPreSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    connection: TelegramDeliveryMethod
    contact: UserContact | None
    # TODO enabled_categories / _kinds


class NotificationSettingsPreSchema(BaseModel):
    # TODO email (enabled_categories / _kinds only)
    telegram: TelegramNotificationSettingsPreSchema | None
    # TODO vk


class TelegramNotificationSettingsSchema(BaseModel):
    connection: TelegramDeliveryMethod.ResponseSchema
    contact: UserContact.ResponseSchema | None


class NotificationSettingsSchema(BaseModel):
    telegram: TelegramNotificationSettingsSchema | None


@router.get(
    path="/users/current/notification-settings/",
    response_model=NotificationSettingsSchema,
    summary="Use `GET /api/protected/notification-service/users/current/delivery-methods/` instead",
    deprecated=True,
)
async def retrieve_notification_settings(
    auth_data: AuthorizationData,
) -> NotificationSettingsPreSchema:
    # TODO delete after frontend switches
    delivery_method = await TelegramDeliveryMethod.find_first_by_user_id(
        auth_data.user_id
    )
    return NotificationSettingsPreSchema(
        telegram=(
            None
            if delivery_method is None
            else TelegramNotificationSettingsPreSchema(
                connection=delivery_method,
                contact=await UserContact.find_first_by_primary_key(
                    user_id=auth_data.user_id,
                    kind=UserContactKind.PERSONAL_TELEGRAM,
                ),
            )
        ),
    )
