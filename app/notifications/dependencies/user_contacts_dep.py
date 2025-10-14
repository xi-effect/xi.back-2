from typing import Annotated

from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.models.user_contacts_db import UserContact


class UserContactResponses(Responses):
    USER_CONTACT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "User contact not found"


@with_responses(UserContactResponses)
async def get_user_contact_by_primary_key(
    user_id: int, contact_kind: UserContactKind
) -> UserContact:
    user_contact = await UserContact.find_first_by_primary_key(
        user_id=user_id, kind=contact_kind
    )
    if user_contact is None:
        raise UserContactResponses.USER_CONTACT_NOT_FOUND
    return user_contact


UserContactByPrimaryKey = Annotated[
    UserContact, Depends(get_user_contact_by_primary_key)
]


@with_responses(UserContactResponses)
async def get_user_contact_for_current_user_by_contact_kind(
    auth_data: AuthorizationData, contact_kind: UserContactKind
) -> UserContact:
    user_contact = await UserContact.find_first_by_primary_key(
        user_id=auth_data.user_id, kind=contact_kind
    )
    if user_contact is None:
        raise UserContactResponses.USER_CONTACT_NOT_FOUND
    return user_contact


CurrentUserContactByContactKind = Annotated[
    UserContact, Depends(get_user_contact_for_current_user_by_contact_kind)
]
