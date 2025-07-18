from app.common.fastapi_ext import APIRouterExt
from app.notifications.models.user_contacts_db import ContactKind, UserContact
from app.notifications.services import telegram_connections_svc, user_contacts_svc

router = APIRouterExt(tags=["user contacts mub"])


@router.post(
    path=f"/users/{{user_id}}/contacts/{ContactKind.PERSONAL_TELEGRAM}/sync-requests/",
    response_model=UserContact.FullSchema | None,
    summary="Sync personal telegram contact for any user by id",
)
async def sync_personal_telegram_contact(user_id: int) -> UserContact | None:
    return await user_contacts_svc.sync_personal_telegram_contact(
        user_id=user_id,
        new_username=await telegram_connections_svc.retrieve_telegram_username_by_user_id(
            user_id=user_id
        ),
    )
