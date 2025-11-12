from typing import Annotated, Any

from fastapi import Body, Depends
from pydantic import BaseModel
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.common.itsdangerous_ext import SignedTokenProvider
from app.users.config import (
    EmailChangeTokenPayloadSchema,
    EmailConfirmationTokenPayloadSchema,
    PasswordResetTokenPayloadSchema,
    email_change_token_provider,
    email_confirmation_token_provider,
    password_reset_token_provider,
)


class TokenVerificationResponses(Responses):
    INVALID_TOKEN = status.HTTP_403_FORBIDDEN, "Invalid token"


def build_email_token_parser_dep[T: BaseModel](
    token_provider: SignedTokenProvider[T],
) -> Any:
    @with_responses(TokenVerificationResponses)
    async def parse_token(token: Annotated[str, Body(embed=True)]) -> T:
        token_payload = token_provider.validate_and_deserialize(token)
        if token_payload is None:
            raise TokenVerificationResponses.INVALID_TOKEN
        return token_payload

    return Depends(parse_token)


EmailConfirmationTokenPayload = Annotated[
    EmailConfirmationTokenPayloadSchema,
    build_email_token_parser_dep(email_confirmation_token_provider),
]

EmailChangeTokenPayload = Annotated[
    EmailChangeTokenPayloadSchema,
    build_email_token_parser_dep(email_change_token_provider),
]

PasswordResetTokenPayload = Annotated[
    PasswordResetTokenPayloadSchema,
    build_email_token_parser_dep(password_reset_token_provider),
]
