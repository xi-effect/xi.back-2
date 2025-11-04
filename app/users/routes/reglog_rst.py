import logging
from typing import Annotated, Final

from fastapi import Depends, Header, Response
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.config import (
    EmailConfirmationTokenPayloadSchema,
    email_confirmation_token_provider,
)
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import add_session_to_response
from app.users.utils.users import (
    UserEmailResponses,
    UsernameResponses,
    is_email_unique,
    is_username_unique,
)

router = APIRouterExt(tags=["reglog"])


TEST_HEADER_NAME: Final[str] = "X-Testing"


def is_cross_site_mode(
    testing: Annotated[str, Header(alias=TEST_HEADER_NAME)] = "",
) -> bool:
    return testing == "true"


CrossSiteMode = Annotated[bool, Depends(is_cross_site_mode)]


@router.post(
    path="/signup/",
    response_model=User.FullSchema,
    responses=Responses.chain(UsernameResponses, UserEmailResponses),
    summary="Register a new account",
)
async def signup(
    data: User.InputSchema,
    is_cross_site: CrossSiteMode,
    response: Response,
) -> User:
    if not await is_email_unique(data.email):
        raise UserEmailResponses.EMAIL_IN_USE
    if not await is_username_unique(data.username):
        raise UsernameResponses.USERNAME_IN_USE

    user = await User.create(**data.model_dump())

    token = email_confirmation_token_provider.serialize_and_sign(
        EmailConfirmationTokenPayloadSchema(user_id=user.id)
    )
    logging.info(
        "Magical send to pochta will happen here",
        extra={
            "message": f"Hi {data.email}! verify email: {token}",
            "email": data.email,
            "token": token,
        },
    )
    user.timeout_email_confirmation_resend()

    session = await Session.create(user=user, is_cross_site=is_cross_site)
    add_session_to_response(response, session)

    return user


class SigninResponses(Responses):
    USER_NOT_FOUND = status.HTTP_401_UNAUTHORIZED, "User not found"
    WRONG_PASSWORD = status.HTTP_401_UNAUTHORIZED, "Wrong password"


@router.post(
    path="/signin/",
    response_model=User.FullSchema,
    responses=SigninResponses.responses(),
    summary="Sign in into an existing account (creates a new session)",
)
async def signin(
    user_data: User.CredentialsSchema,
    is_cross_site: CrossSiteMode,
    response: Response,
) -> User:
    user = await User.find_first_by_kwargs(email=user_data.email)
    if user is None:
        raise SigninResponses.USER_NOT_FOUND

    if not user.is_password_valid(user_data.password):
        raise SigninResponses.WRONG_PASSWORD

    session = await Session.create(user=user, is_cross_site=is_cross_site)
    add_session_to_response(response, session)
    await Session.cleanup_by_user(user.id)

    return user
