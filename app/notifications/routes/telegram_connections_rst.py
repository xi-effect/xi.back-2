from aiogram.utils.deep_linking import create_start_link
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.notifications.config import telegram_app, telegram_deep_link_provider
from app.notifications.models.telegram_connections_db import TelegramConnection

router = APIRouterExt(tags=["telegram connections"])


class ExistingTelegramConnectionResponses(Responses):
    TELEGRAM_CONNECTION_ALREADY_EXISTS = (
        status.HTTP_409_CONFLICT,
        "Telegram connection already exists",
    )


@router.post(
    path="/users/current/telegram-connection-requests/",
    response_model=str,
    responses=ExistingTelegramConnectionResponses.responses(),
    summary="Generate a link for connecting telegram notifications for the current user",
)
async def generate_telegram_connection_link(auth_data: AuthorizationData) -> str:
    telegram_connection = await TelegramConnection.find_first_by_id(auth_data.user_id)
    if telegram_connection is not None:
        raise ExistingTelegramConnectionResponses.TELEGRAM_CONNECTION_ALREADY_EXISTS

    return await create_start_link(
        bot=telegram_app.bot,
        payload=telegram_deep_link_provider.create_signed_link_payload(
            user_id=auth_data.user_id
        ),
    )


class TelegramConnectionResponses(Responses):
    TELEGRAM_CONNECTION_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "Telegram connection not found",
    )


@router.delete(
    path="/users/current/telegram-connection/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=TelegramConnectionResponses.responses(),
    summary="Remove telegram connection for the current user",
)
async def remove_telegram_connection(auth_data: AuthorizationData) -> None:
    telegram_connection = await TelegramConnection.find_first_by_id(auth_data.user_id)
    if telegram_connection is None:
        raise TelegramConnectionResponses.TELEGRAM_CONNECTION_NOT_FOUND
    await telegram_connection.delete()
