from collections.abc import Sequence
from typing import Annotated

from fastapi import Body

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.notifications.dependencies.user_contacts_dep import (
    CurrentUserContactByContactKind,
)
from app.notifications.models.user_contacts_db import UserContact

router = APIRouterExt(tags=["user contacts"])


@router.get(
    path="/users/current/contacts/",
    response_model=list[UserContact.FullSchema],
    summary="List all contacts for the current user",
)
async def list_user_contacts(auth_data: AuthorizationData) -> Sequence[UserContact]:
    return await UserContact.find_all_by_user(user_id=auth_data.user_id)


@router.put(
    path="/users/current/contacts/{contact_kind}/visibility/",
    response_model=UserContact.FullSchema,
    summary="Set current user's contact's visibility by contact kind",
)
async def update_user_contact_visibility(
    user_contact: CurrentUserContactByContactKind,
    is_public: Annotated[bool, Body(embed=True)],
) -> UserContact:
    user_contact.is_public = is_public
    return user_contact
