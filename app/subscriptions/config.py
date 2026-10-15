from app.common.config import settings
from app.subscriptions.utils.yookassa_client import YooKassaClient

yookassa_client = YooKassaClient(
    base_url=settings.yookassa_server_base_url,
    shop_id=settings.yookassa_shop_id,
    secret_key=settings.yookassa_secret_key,
)
