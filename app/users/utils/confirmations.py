from pydantic import BaseModel
from starlette import status

from app.common.fastapi_ext import Responses


class TokenVerificationResponses(Responses):
    INVALID_TOKEN = status.HTTP_401_UNAUTHORIZED, "Invalid token"


class ConfirmationTokenData(BaseModel):
    token: str


class EmailResendResponses(Responses):
    TOO_MANY_EMAILS = status.HTTP_429_TOO_MANY_REQUESTS, "Too many emails"
