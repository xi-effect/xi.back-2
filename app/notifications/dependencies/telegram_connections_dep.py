from typing import Annotated

from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.notifications.models.telegram_connections_db import TelegramConnection


class TelegramConnectionResponses(Responses):
    TELEGRAM_CONNECTION_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "Telegram connection not found",
    )


@with_responses(TelegramConnectionResponses)
async def get_telegram_connection_by_user_id(user_id: int) -> TelegramConnection:
    telegram_connection = await TelegramConnection.find_first_by_id(user_id)
    if telegram_connection is None:
        raise TelegramConnectionResponses.TELEGRAM_CONNECTION_NOT_FOUND
    return telegram_connection


TelegramConnectionByUserID = Annotated[
    TelegramConnection, Depends(get_telegram_connection_by_user_id)
]


@with_responses(TelegramConnectionResponses)
async def get_telegram_connection_for_current_user(
    auth_data: AuthorizationData,
) -> TelegramConnection:
    telegram_connection = await TelegramConnection.find_first_by_id(auth_data.user_id)
    if telegram_connection is None:
        raise TelegramConnectionResponses.TELEGRAM_CONNECTION_NOT_FOUND
    return telegram_connection


CurrentUserTelegramConnection = Annotated[
    TelegramConnection, Depends(get_telegram_connection_for_current_user)
]


class ExistingTelegramConnectionResponses(Responses):
    TELEGRAM_CONNECTION_ALREADY_EXISTS = (
        status.HTTP_409_CONFLICT,
        "Telegram connection already exists",
    )


@with_responses(ExistingTelegramConnectionResponses)
async def check_telegram_connection_already_exists_for_current_user(
    auth_data: AuthorizationData,
) -> None:
    telegram_connection = await TelegramConnection.find_first_by_id(auth_data.user_id)
    if telegram_connection is not None:
        raise ExistingTelegramConnectionResponses.TELEGRAM_CONNECTION_ALREADY_EXISTS


@with_responses(ExistingTelegramConnectionResponses)
async def check_telegram_connection_already_exists_by_user_id(user_id: int) -> None:
    telegram_connection = await TelegramConnection.find_first_by_id(user_id)
    if telegram_connection is not None:
        raise ExistingTelegramConnectionResponses.TELEGRAM_CONNECTION_ALREADY_EXISTS
