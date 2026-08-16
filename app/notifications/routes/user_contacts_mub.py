from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.notifications.dependencies.delivery_methods_dep import (
    MessengerDeliveryMethodByKindAndID,
)
from app.notifications.models.delivery_methods_db import DeliveryMethodStatus
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services import user_contacts_svc

router = APIRouterExt(tags=["user contacts mub"])


class InactiveDeliveryMethodResponses(Responses):
    DELIVERY_METHOD_NOT_ACTIVE = (
        status.HTTP_409_CONFLICT,
        "Delivery method is not active",
    )


@router.post(
    path=(
        "/users/{user_id}/delivery-methods/{delivery_method_kind}"
        "/user-contact/sync-requests/"
    ),
    response_model=UserContact.FullSchema | None,
    responses=InactiveDeliveryMethodResponses.responses(),
    summary="Sync messenger user contact for any user by id and kind",
)
async def sync_messenger_user_contact(
    delivery_method: MessengerDeliveryMethodByKindAndID,
) -> UserContact | None:
    if delivery_method.status is not DeliveryMethodStatus.ACTIVE:
        raise InactiveDeliveryMethodResponses.DELIVERY_METHOD_NOT_ACTIVE

    return await user_contacts_svc.delivery_method_to_user_contact_syncer(
        delivery_method=delivery_method
    ).sync_with_origin()
