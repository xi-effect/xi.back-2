from aiogram.utils.deep_linking import create_deep_link
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.notifications.config import telegram_app, telegram_deep_link_provider
from app.notifications.dependencies.delivery_methods_dep import (
    DeliveryMethodResponses,
    MissingTelegramDeliveryMethodDep,
)
from app.notifications.models.delivery_methods_db import TelegramDeliveryMethod
from app.notifications.services import user_contacts_svc

router = APIRouterExt(tags=["telegram connections"])


@router.post(
    path="/users/current/telegram-connection-requests/",
    response_model=str,
    summary="Use `POST /api/protected/notification-service/users/current/delivery-methods/telegram/connection-requests/` instead",
    dependencies=[MissingTelegramDeliveryMethodDep],
    deprecated=True,
)
async def generate_telegram_connection_link(
    auth_data: AuthorizationData,
) -> str:
    return create_deep_link(
        username=telegram_app.bot_username,
        link_type="start",
        payload=telegram_deep_link_provider.create_signed_link_payload(
            user_id=auth_data.user_id
        ),
    )


@router.delete(
    path="/users/current/telegram-connection/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=DeliveryMethodResponses.responses(),
    summary="Use `DELETE /api/protected/notification-service/users/current/delivery-methods/{delivery_method_kind}/` instead",
    deprecated=True,
)
async def remove_telegram_connection(
    auth_data: AuthorizationData,
) -> None:
    delivery_method = await TelegramDeliveryMethod.find_first_by_user_id(
        user_id=auth_data.user_id
    )
    if delivery_method is None:
        raise DeliveryMethodResponses.DELIVERY_METHOD_NOT_FOUND
    await delivery_method.delete()
    await user_contacts_svc.remove_personal_telegram_contact(
        user_id=delivery_method.peer_id
    )
