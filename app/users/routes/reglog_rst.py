from typing import Annotated, Final

from fastapi import Depends, Header, Response
from starlette import status

from app.common.config_bdg import notifications_bridge, pochta_bridge
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.pochta_sch import (
    EmailMessageInputSchema,
    EmailMessageKind,
    TokenEmailMessagePayloadSchema,
)
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

    await notifications_bridge.create_or_update_email_connection(
        user_id=user.id,
        email=user.email,
    )

    token = email_confirmation_token_provider.serialize_and_sign(
        EmailConfirmationTokenPayloadSchema(user_id=user.id)
    )
    await pochta_bridge.send_email_message(
        EmailMessageInputSchema(
            payload=TokenEmailMessagePayloadSchema(
                kind=EmailMessageKind.EMAIL_CONFIRMATION_V2,
                token=token,
            ),
            recipient_emails=[user.email],
        )
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
