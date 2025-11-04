import logging

from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.config import (
    EmailConfirmationTokenPayloadSchema,
    email_confirmation_token_provider,
)
from app.users.dependencies.email_rate_limit_dep import EmailRateLimitResponses
from app.users.dependencies.email_token_dep import (
    EmailConfirmationTokenPayload,
    TokenVerificationResponses,
)
from app.users.dependencies.users_dep import AuthorizedUser
from app.users.models.users_db import OnboardingStage, User

protected_router = APIRouterExt(tags=["email confirmation"])
public_router = APIRouterExt(tags=["email confirmation"])


class EmailConfirmationResponses(Responses):
    ALREADY_CONFIRMED = status.HTTP_409_CONFLICT, "Email already confirmed"


@protected_router.post(
    path="/users/current/email-confirmation/requests/",
    status_code=status.HTTP_202_ACCEPTED,
    responses=Responses.chain(EmailRateLimitResponses, EmailConfirmationResponses),
    summary="Request to resend email confirmation for the current user",
)
async def request_email_confirmation_resend(user: AuthorizedUser) -> None:
    if user.onboarding_stage is not OnboardingStage.EMAIL_CONFIRMATION:
        raise EmailConfirmationResponses.ALREADY_CONFIRMED

    if not user.is_email_confirmation_resend_allowed():
        raise EmailRateLimitResponses.TOO_MANY_EMAILS

    token = email_confirmation_token_provider.serialize_and_sign(
        EmailConfirmationTokenPayloadSchema(user_id=user.id)
    )
    logging.info(
        "Magical send to pochta will happen here",
        extra={
            "message": f"Hi {user.email}, verify email: {token}",
            "email": user.email,
            "token": token,
        },
    )

    user.timeout_email_confirmation_resend()


@public_router.post(
    path="/email-confirmation/confirmations/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=EmailConfirmationResponses.responses(),
    summary="Confirm user's email",
)
async def confirm_email(token_payload: EmailConfirmationTokenPayload) -> None:
    user = await User.find_first_by_id(token_payload.user_id)
    if user is None:
        raise TokenVerificationResponses.INVALID_TOKEN

    if user.onboarding_stage is not OnboardingStage.EMAIL_CONFIRMATION:
        raise EmailConfirmationResponses.ALREADY_CONFIRMED

    user.onboarding_stage = OnboardingStage.USER_INFORMATION
