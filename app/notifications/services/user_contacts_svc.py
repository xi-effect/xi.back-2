from aiogram.utils.link import create_telegram_link

from app.notifications.models.user_contacts_db import ContactKind, UserContact


async def remove_personal_telegram_contact(user_id: int) -> None:
    await UserContact.delete_by_kwargs(
        user_id=user_id,
        kind=ContactKind.PERSONAL_TELEGRAM,
    )


async def sync_personal_telegram_contact(
    user_id: int,
    new_username: str | None,
) -> None:
    if new_username is None:
        return await remove_personal_telegram_contact(user_id=user_id)

    telegram_contact_link = create_telegram_link(new_username)
    telegram_contact_title = f"@{new_username}"

    user_contact = await UserContact.find_first_by_primary_key(
        user_id=user_id,
        kind=ContactKind.PERSONAL_TELEGRAM,
    )

    if user_contact is None:
        await UserContact.create(
            user_id=user_id,
            kind=ContactKind.PERSONAL_TELEGRAM,
            link=telegram_contact_link,
            title=telegram_contact_title,
            is_public=True,
        )
    else:
        user_contact.update(
            link=telegram_contact_link,
            title=telegram_contact_title,
        )
