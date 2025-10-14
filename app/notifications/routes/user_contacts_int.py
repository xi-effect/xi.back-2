from collections.abc import Sequence

from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.user_contacts_sch import UserContactKind, UserContactSchema
from app.notifications.dependencies.user_contacts_dep import UserContactByPrimaryKey
from app.notifications.models.user_contacts_db import UserContact

router = APIRouterExt(tags=["user contacts internal"])


@router.get(
    path="/users/{user_id}/contacts/",
    response_model=list[UserContactSchema],
    summary="List all user contacts by user id",
)
async def list_user_contacts(
    user_id: int, public_only: bool = False
) -> Sequence[UserContact]:
    return await UserContact.find_all_by_user(user_id=user_id, public_only=public_only)


@router.put(
    path="/users/{user_id}/contacts/{contact_kind}/",
    response_model=UserContactSchema,
    summary="Update user contact by user id & contact kind",
)
async def update_user_contact(
    user_id: int,
    contact_kind: UserContactKind,
    data: UserContact.InputSchema,
) -> UserContact:
    user_contact = await UserContact.find_first_by_primary_key(
        user_id=user_id,
        kind=contact_kind,
    )
    if user_contact is None:
        return await UserContact.create(
            **data.model_dump(),
            user_id=user_id,
            kind=contact_kind,
        )
    user_contact.update(**data.model_dump())
    return user_contact


@router.delete(
    path="/users/{user_id}/contacts/{contact_kind}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user contact by user id & contact kind",
)
async def delete_user_contact(user_contact: UserContactByPrimaryKey) -> None:
    await user_contact.delete()
