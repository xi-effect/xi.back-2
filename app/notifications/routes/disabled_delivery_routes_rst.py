from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)

router = APIRouterExt(tags=["disabled delivery routes"])


@router.put(
    path=(
        "/users/current"
        "/delivery-methods/{delivery_method_kind}"
        "/enabled-notification-categories/{notification_category}/"
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    summary=(
        "Enable sending notifications of this notification group "
        "via a delivery method by kind for the current user"
    ),
)
async def enable_delivery_route(
    auth_data: AuthorizationData,
    delivery_method_kind: DeliveryMethodKind,
    notification_category: NotificationCategory,
) -> None:
    await DisabledDeliveryRoute.enable_by_primary_key(
        user_id=auth_data.user_id,
        delivery_method_kind=delivery_method_kind,
        notification_category=notification_category,
    )


@router.delete(
    path=(
        "/users/current"
        "/delivery-methods/{delivery_method_kind}"
        "/enabled-notification-categories/{notification_category}/"
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    summary=(
        "Disable sending notifications of this notification group "
        "via a delivery method by kind for the current user"
    ),
)
async def disable_delivery_route(
    auth_data: AuthorizationData,
    delivery_method_kind: DeliveryMethodKind,
    notification_category: NotificationCategory,
) -> None:
    await DisabledDeliveryRoute.disable_by_primary_key(
        user_id=auth_data.user_id,
        delivery_method_kind=delivery_method_kind,
        notification_category=notification_category,
    )
