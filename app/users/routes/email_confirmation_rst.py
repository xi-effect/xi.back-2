from app.common.config import email_confirmation_cryptography
from app.common.fastapi_ext import APIRouterExt
from app.users.models.users_db import User
from app.users.utils.confirmations import (
    ConfirmationTokenData,
    TokenVerificationResponses,
)

router = APIRouterExt(tags=["email confirmation"])


@router.post(
    "/email-confirmation/confirmations/",
    responses=TokenVerificationResponses.responses(),
    summary="Confirm user's email",
    status_code=204,
)
async def confirm_email(confirmation_token: ConfirmationTokenData) -> None:
    email: str | None = email_confirmation_cryptography.decrypt(
        confirmation_token.token
    )
    if email is None:
        raise TokenVerificationResponses.INVALID_TOKEN
    user = await User.find_first_by_kwargs(email=email)
    if user is None:
        raise TokenVerificationResponses.INVALID_TOKEN
    user.email_confirmed = True
