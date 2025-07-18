from app.common.aiogram_ext import TelegramApp
from app.common.config import settings
from app.notifications.utils.deep_links import TelegramDeepLinkProvider

telegram_app = TelegramApp()
telegram_deep_link_provider = TelegramDeepLinkProvider(
    secret_keys=settings.telegram_connection_token_keys.keys,
    ttl=settings.telegram_connection_token_keys.encryption_ttl,
)
