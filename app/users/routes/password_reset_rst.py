import logging
from typing import Annotated

from fastapi import Body
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.users.config import (
    PasswordResetTokenPayloadSchema,
    password_reset_token_provider,
)
from app.users.dependencies.email_token_dep import (
    PasswordResetTokenPayload,
    TokenVerificationResponses,
)
from app.users.dependencies.users_dep import TargetUserResponses
from app.users.models.users_db import User

router = APIRouterExt(tags=["password reset"])


@router.post(
    path="/password-reset/requests/",
    status_code=status.HTTP_202_ACCEPTED,
    responses=TargetUserResponses.responses(),
    summary="Request for a password reset",
)
async def request_password_reset(data: User.EmailSchema) -> None:
    user = await User.find_first_by_kwargs(email=data.email)
    if user is None:
        raise TargetUserResponses.USER_NOT_FOUND

    token = password_reset_token_provider.serialize_and_sign(
        PasswordResetTokenPayloadSchema(
            user_id=user.id,
            password_last_changed_at=user.password_last_changed_at,
        )
    )
    logging.info(
        "Magical send to pochta will happen here",
        extra={
            "message": f"Hi {data.email}! reset_token: {token}",
            "email": data.email,
            "token": token,
        },
    )


@router.post(
    path="/password-reset/confirmations/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Confirm password reset and set a new password",
)
async def confirm_password_reset(
    token_payload: PasswordResetTokenPayload,
    new_password: Annotated[str, Body(embed=True, min_length=6, max_length=100)],
) -> None:
    user = await User.find_first_by_id(token_payload.user_id)
    if user is None:
        raise TokenVerificationResponses.INVALID_TOKEN
    if user.password_last_changed_at != token_payload.password_last_changed_at:
        raise TokenVerificationResponses.INVALID_TOKEN

    user.change_password(password=new_password)
