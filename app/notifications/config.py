from app.common.aiogram_ext import TelegramApp
from app.common.config import settings
from app.notifications.utils.deep_links import DeepLinkProvider
from app.notifications.utils.vk_app import VKApp

telegram_app = TelegramApp()
vk_app = VKApp()

telegram_deep_link_provider = DeepLinkProvider(
    secret_keys=settings.telegram_connection_token_keys.keys,
    ttl=settings.telegram_connection_token_keys.encryption_ttl,
)
vk_connection_key_provider = DeepLinkProvider(
    secret_keys=settings.vk_connection_token_keys.keys,
    ttl=settings.vk_connection_token_keys.encryption_ttl,
)
