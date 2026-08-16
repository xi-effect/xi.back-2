from starlette import status

from app.common.fastapi_ext import Responses


class WebhookTokenResponses(Responses):
    INVALID_WEBHOOK_TOKEN = status.HTTP_401_UNAUTHORIZED, "Invalid webhook token"
