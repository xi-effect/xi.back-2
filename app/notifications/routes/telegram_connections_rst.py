from aiogram.utils.deep_linking import create_start_link

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.notifications.config import telegram_app, telegram_deep_link_provider

router = APIRouterExt(tags=["telegram connections"])


@router.post(
    path="/users/current/telegram-connection-requests/",
    response_model=str,
    summary="Generate a link for connecting telegram notifications for the current user",
)
async def generate_telegram_connection_link(auth_data: AuthorizationData) -> str:
    return await create_start_link(
        bot=telegram_app.bot,
        payload=telegram_deep_link_provider.create_signed_link_payload(
            user_id=auth_data.user_id
        ),
    )
