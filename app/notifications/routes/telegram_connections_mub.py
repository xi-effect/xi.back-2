from aiogram.utils.deep_linking import create_deep_link
from fastapi import Depends
from pydantic import BaseModel
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.notifications.config import telegram_app, telegram_deep_link_provider
from app.notifications.dependencies.telegram_connections_dep import (
    TelegramConnectionByUserID,
    check_telegram_connection_already_exists_by_user_id,
)
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)

router = APIRouterExt(tags=["telegram connections mub"])


@router.post(
    path="/users/{user_id}/telegram-connection-requests/",
    response_model=str,
    summary="Generate a link for connecting telegram notifications for any user by id",
    dependencies=[Depends(check_telegram_connection_already_exists_by_user_id)],
)
async def generate_telegram_connection_link(user_id: int) -> str:
    return create_deep_link(
        username=telegram_app.bot_username,
        link_type="start",
        payload=telegram_deep_link_provider.create_signed_link_payload(user_id=user_id),
    )


@router.post(
    path="/users/{user_id}/telegram-connection/",
    status_code=status.HTTP_201_CREATED,
    response_model=TelegramConnection.ResponseMUBSchema,
    summary="Create a telegram connection for any user by id",
    dependencies=[Depends(check_telegram_connection_already_exists_by_user_id)],
)
async def create_telegram_connection(
    user_id: int,
    data: TelegramConnection.InputMUBSchema,
) -> TelegramConnection:
    return await TelegramConnection.create(
        user_id=user_id,
        **data.model_dump(),
    )


@router.get(
    path="/users/{user_id}/telegram-connection/",
    response_model=TelegramConnection.ResponseMUBSchema,
    summary="Retrieve any telegram connection by user id",
)
async def retrieve_telegram_connection(
    telegram_connection: TelegramConnectionByUserID,
) -> TelegramConnection:
    return telegram_connection


@router.patch(
    path="/users/{user_id}/telegram-connection/",
    response_model=TelegramConnection.ResponseMUBSchema,
    summary="Update any telegram connection by user id",
)
async def patch_telegram_connection(
    telegram_connection: TelegramConnectionByUserID,
    data: TelegramConnection.PatchMUBSchema,
) -> TelegramConnection:
    telegram_connection.update(**data.model_dump(exclude_defaults=True))
    return telegram_connection


@router.delete(
    path="/users/{user_id}/telegram-connection/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any telegram connection by user id",
)
async def delete_telegram_connection(
    telegram_connection: TelegramConnectionByUserID,
) -> None:
    await telegram_connection.delete()


class ActiveTelegramConnectionResponses(Responses):
    TELEGRAM_CONNECTION_IS_NOT_ACTIVE = (
        status.HTTP_409_CONFLICT,
        "Telegram connection is not active",
    )


class TelegramMessageSchema(BaseModel):
    text: str


@router.post(
    path="/users/{user_id}/telegram-connection/messages/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ActiveTelegramConnectionResponses.responses(),
    summary="Send a message in telegram to any user by id (if connection is active)",
)
async def send_message_to_user_via_telegram(
    telegram_connection: TelegramConnectionByUserID,
    data: TelegramMessageSchema,
) -> None:
    if telegram_connection.status is not TelegramConnectionStatus.ACTIVE:
        raise ActiveTelegramConnectionResponses.TELEGRAM_CONNECTION_IS_NOT_ACTIVE

    await telegram_app.bot.send_message(
        chat_id=telegram_connection.chat_id,
        **data.model_dump(),
    )
