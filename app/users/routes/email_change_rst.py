import logging
from typing import Annotated

from fastapi import Body
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.config import (
    EmailChangeTokenPayloadSchema,
    email_change_token_provider,
)
from app.users.dependencies.email_rate_limit_dep import EmailRateLimitResponses
from app.users.dependencies.email_token_dep import (
    EmailChangeTokenPayload,
    TokenVerificationResponses,
)
from app.users.dependencies.password_protected_dep import PasswordProtected
from app.users.dependencies.users_dep import AuthorizedUser
from app.users.models.users_db import User
from app.users.utils.users import UserEmailResponses, is_email_unique

protected_router = APIRouterExt(tags=["email change"])
public_router = APIRouterExt(tags=["email change"])


@protected_router.post(
    path="/users/current/email-change/requests/",
    status_code=status.HTTP_202_ACCEPTED,
    responses=Responses.chain(
        UserEmailResponses,
        EmailRateLimitResponses,
    ),
    summary="Request to update current user's email (send confirmation email)",
    dependencies=[PasswordProtected],
)
async def request_email_change(
    user: AuthorizedUser,
    new_email: Annotated[str, Body(embed=True, max_length=100)],
) -> None:
    if not await is_email_unique(new_email):
        raise UserEmailResponses.EMAIL_IN_USE

    if not user.is_email_confirmation_resend_allowed():
        raise EmailRateLimitResponses.TOO_MANY_EMAILS

    token: str = email_change_token_provider.serialize_and_sign(
        EmailChangeTokenPayloadSchema(
            user_id=user.id,
            new_email=new_email,
        )
    )
    logging.info(
        "Magical send to pochta will happen here",
        extra={
            "message": f"Your email has been changed to {token},"
            + f"confirm new email: {token}",
            "new_email": new_email,
            "token": token,
        },
    )

    user.timeout_email_confirmation_resend()


@public_router.post(
    path="/email-change/confirmations/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=UserEmailResponses.responses(),
    summary="Confirm email change and update user's email",
)
async def confirm_email_change(token_payload: EmailChangeTokenPayload) -> None:
    user = await User.find_first_by_id(token_payload.user_id)
    if user is None:
        raise TokenVerificationResponses.INVALID_TOKEN

    if not await is_email_unique(token_payload.new_email):
        raise UserEmailResponses.EMAIL_IN_USE

    user.email = token_payload.new_email
