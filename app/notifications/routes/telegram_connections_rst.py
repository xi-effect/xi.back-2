from aiogram.utils.deep_linking import create_deep_link
from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.notifications.config import telegram_app, telegram_deep_link_provider
from app.notifications.dependencies.telegram_connections_dep import (
    CurrentUserTelegramConnection,
    check_telegram_connection_already_exists_for_current_user,
)
from app.notifications.services import user_contacts_svc

router = APIRouterExt(tags=["telegram connections"])


@router.post(
    path="/users/current/telegram-connection-requests/",
    response_model=str,
    summary="Generate a link for connecting telegram notifications for the current user",
    dependencies=[Depends(check_telegram_connection_already_exists_for_current_user)],
)
async def generate_telegram_connection_link(auth_data: AuthorizationData) -> str:
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
    summary="Remove telegram connection for the current user",
)
async def remove_telegram_connection(
    telegram_connection: CurrentUserTelegramConnection,
) -> None:
    await telegram_connection.delete()
    await user_contacts_svc.remove_personal_telegram_contact(
        user_id=telegram_connection.user_id
    )
