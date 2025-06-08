import logging
from typing import Annotated

from pydantic import Field
from starlette import status

from app.common.config import password_reset_cryptography
from app.common.fastapi_ext import APIRouterExt
from app.users.dependencies.users_dep import TargetUserResponses
from app.users.models.users_db import User
from app.users.utils.confirmations import (
    ConfirmationTokenData,
    TokenVerificationResponses,
)

router = APIRouterExt(tags=["password reset"])


@router.post(
    "/password-reset/requests/",
    responses=TargetUserResponses.responses(),
    summary="Request for a password reset",
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_password_reset(data: User.EmailSchema) -> None:
    user = await User.find_first_by_kwargs(email=data.email)
    if user is None:
        raise TargetUserResponses.USER_NOT_FOUND
    reset_token = password_reset_cryptography.encrypt(user.generated_reset_token)
    logging.info(
        "Magical send to pochta will happen here",
        extra={
            "message": f"Hi {data.email}! reset_token: {reset_token}",
            "email": data.email,
            "token": reset_token,
        },
    )


class ResetCredentials(ConfirmationTokenData):
    new_password: Annotated[str, Field(min_length=6, max_length=100)]


@router.post(
    "/password-reset/confirmations/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=TokenVerificationResponses.responses(),
    summary="Confirm password reset and set a new password",
)
async def confirm_password_reset(reset_data: ResetCredentials) -> None:
    token = password_reset_cryptography.decrypt(reset_data.token)
    if token is None:
        raise TokenVerificationResponses.INVALID_TOKEN
    user = await User.find_first_by_kwargs(reset_token=token)
    if user is None:
        raise TokenVerificationResponses.INVALID_TOKEN
    user.reset_password(password=reset_data.new_password)
