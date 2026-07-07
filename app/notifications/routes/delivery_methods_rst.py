from typing import Literal

from aiogram.utils.deep_linking import create_deep_link
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.config import (
    telegram_app,
    telegram_deep_link_provider,
)
from app.notifications.dependencies.delivery_methods_dep import (
    MissingTelegramDeliveryMethodDep,
    MyDeliveryMethodByKind,
)
from app.notifications.services import user_contacts_svc

router = APIRouterExt(tags=["delivery methods"])


@router.post(
    path=f"/users/current/delivery-methods/{DeliveryMethodKind.TELEGRAM}/connection-requests/",
    dependencies=[MissingTelegramDeliveryMethodDep],
    summary="Generate a link for connecting telegram notifications for the current user",
)
async def generate_telegram_connection_link(auth_data: AuthorizationData) -> str:
    return create_deep_link(
        username=telegram_app.bot_username,
        link_type="start",
        payload=telegram_deep_link_provider.create_signed_link_payload(
            user_id=auth_data.user_id,
        ),
    )


DeletableDeliveryMethodKind = Literal[DeliveryMethodKind.TELEGRAM]


@router.delete(
    path="/users/current/delivery-methods/{delivery_method_kind}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any delivery method by kind for the current user",
)
async def delete_delivery_method(delivery_method: MyDeliveryMethodByKind) -> None:
    await delivery_method.delete()
    await user_contacts_svc.remove_personal_telegram_contact(
        user_id=delivery_method.user_id
    )  # TODO redo for vk
