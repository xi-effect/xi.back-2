import logging
from typing import Annotated

from pydantic import Field
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT

from app.common.config import email_confirmation_cryptography
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.users_dep import AuthorizedUser
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.confirmations import EmailResendResponses
from app.users.utils.users import (
    UserEmailResponses,
    UsernameResponses,
    is_email_unique,
    is_username_unique,
)

router = APIRouterExt(tags=["current user"])


@router.get(
    "/users/current/home/",
    response_model=User.FullSchema,
    summary="Retrieve current user's profile data",
)
async def get_user_data(user: AuthorizedUser) -> User:
    return user


@router.patch(
    "/users/current/profile/",
    response_model=User.FullSchema,
    responses=UsernameResponses.responses(),
    summary="Update current user's profile data",
)
async def patch_user_data(
    patch_data: User.ProfilePatchSchema, user: AuthorizedUser
) -> User:
    if not await is_username_unique(patch_data.username, user.username):
        raise UsernameResponses.USERNAME_IN_USE.value
    user.update(**patch_data.model_dump(exclude_defaults=True))
    return user


@router.post(
    "/users/current/email-confirmation-requests/",
    responses=EmailResendResponses.responses(),
    summary="Resend email confirmation message for the current user",
    status_code=204,
)
async def resend_email_confirmation(user: AuthorizedUser) -> None:
    if not user.is_email_confirmation_resend_allowed():
        raise EmailResendResponses.TOO_MANY_EMAILS
    confirmation_token: str = email_confirmation_cryptography.encrypt(user.email)
    user.set_confirmation_resend_timeout()
    logging.info(
        "Magical send to pochta will happen here",
        extra={
            "message": f"Hi {user.email}, verify email: {confirmation_token}",
            "email": user.email,
            "token": confirmation_token,
        },
    )


class PasswordProtectedResponses(Responses):
    WRONG_PASSWORD = (HTTP_401_UNAUTHORIZED, "Wrong password")


class EmailChangeSchema(User.PasswordSchema):
    new_email: Annotated[str, Field(max_length=100)]


@router.put(
    "/users/current/email/",
    response_model=User.FullSchema,
    responses=Responses.chain(
        PasswordProtectedResponses, UserEmailResponses, EmailResendResponses
    ),
    summary="Update current user's email",
)
async def change_user_email(user: AuthorizedUser, put_data: EmailChangeSchema) -> User:
    if not user.is_password_valid(password=put_data.password):
        raise PasswordProtectedResponses.WRONG_PASSWORD.value

    if not await is_email_unique(put_data.new_email, user.username):
        raise UserEmailResponses.EMAIL_IN_USE.value

    if not user.is_email_confirmation_resend_allowed():
        raise EmailResendResponses.TOO_MANY_EMAILS

    user.email = put_data.new_email
    user.email_confirmed = False
    user.set_confirmation_resend_timeout()
    confirmation_token: str = email_confirmation_cryptography.encrypt(user.email)
    logging.info(
        "Magical send to pochta will happen here",
        extra={
            "message": f"Your email has been changed to {put_data.new_email},"
            + f"confirm new email: {confirmation_token}",
            "new_email": put_data.new_email,
            "token": confirmation_token,
        },
    )

    return user


class PasswordChangeSchema(User.PasswordSchema):
    new_password: Annotated[str, Field(min_length=6, max_length=100)]


class PasswordChangeResponses(Responses):
    PASSWORD_MATCHES_CURRENT = (
        HTTP_409_CONFLICT,
        "New password matches the current one",
    )


@router.put(
    "/users/current/password/",
    response_model=User.FullSchema,
    responses=Responses.chain(PasswordChangeResponses, PasswordProtectedResponses),
    summary="Update current user's password",
)
async def change_user_password(
    user: AuthorizedUser, auth_data: AuthorizationData, put_data: PasswordChangeSchema
) -> User:
    if not user.is_password_valid(password=put_data.password):
        raise PasswordProtectedResponses.WRONG_PASSWORD

    if user.is_password_valid(put_data.new_password):
        raise PasswordChangeResponses.PASSWORD_MATCHES_CURRENT

    user.change_password(put_data.new_password)
    await Session.disable_all_but_one_for_user(
        user_id=auth_data.user_id, excluded_id=auth_data.session_id
    )

    return user
