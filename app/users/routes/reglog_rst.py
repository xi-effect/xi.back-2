import logging

from fastapi import Response
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import email_confirmation_cryptography
from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import (
    AuthorizedSession,
    CrossSiteMode,
    add_session_to_response,
    remove_session_from_response,
)
from app.users.utils.users import (
    UserEmailResponses,
    UsernameResponses,
    is_email_unique,
    is_username_unique,
)

router = APIRouterExt(tags=["reglog"])


@router.post(
    "/signup/",
    response_model=User.FullModel,
    responses=Responses.chain(UsernameResponses, UserEmailResponses),
    summary="Register a new account",
)
async def signup(
    user_data: User.InputModel, cross_site: CrossSiteMode, response: Response
) -> User:
    if not await is_email_unique(user_data.email):
        raise UserEmailResponses.EMAIL_IN_USE.value
    if not await is_username_unique(user_data.username):
        raise UsernameResponses.USERNAME_IN_USE.value

    user = await User.create(**user_data.model_dump())

    confirmation_token: str = email_confirmation_cryptography.encrypt(user.email)
    logging.info(
        "Magical send to pochta will happen here",
        extra={
            "message": f"Hi {user_data.email}! reset_token: {confirmation_token}",
            "email": user_data.email,
            "token": confirmation_token,
        },
    )

    session = await Session.create(user=user, cross_site=cross_site)
    add_session_to_response(response, session)

    return user


class SigninResponses(Responses):
    USER_NOT_FOUND = (HTTP_401_UNAUTHORIZED, User.not_found_text)
    WRONG_PASSWORD = (HTTP_401_UNAUTHORIZED, "Wrong password")


@router.post(
    "/signin/",
    response_model=User.FullModel,
    responses=SigninResponses.responses(),
    summary="Sign in into an existing account (creates a new session)",
)
async def signin(
    user_data: User.CredentialsModel, cross_site: CrossSiteMode, response: Response
) -> User:
    user = await User.find_first_by_kwargs(email=user_data.email)
    if user is None:
        raise SigninResponses.USER_NOT_FOUND.value

    if not user.is_password_valid(user_data.password):
        raise SigninResponses.WRONG_PASSWORD.value

    session = await Session.create(user=user, cross_site=cross_site)
    add_session_to_response(response, session)
    await Session.cleanup_by_user(user.id)

    return user


@router.post(
    "/signout/",
    status_code=204,
    summary="Sign out from current account (disables the current session and removes cookies)",
)
async def signout(session: AuthorizedSession, response: Response) -> None:
    session.disabled = True
    remove_session_from_response(response)
