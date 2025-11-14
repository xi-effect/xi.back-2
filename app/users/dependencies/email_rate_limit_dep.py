from starlette import status

from app.common.fastapi_ext import Responses


class EmailRateLimitResponses(Responses):
    TOO_MANY_EMAILS = status.HTTP_429_TOO_MANY_REQUESTS, "Too many emails"
