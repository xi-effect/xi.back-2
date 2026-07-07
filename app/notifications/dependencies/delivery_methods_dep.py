from typing import Annotated, cast

from fastapi import Depends, Path
from fastapi.params import Depends as DependsType
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.delivery_methods_db import (
    DeliveryMethod,
)


class DeliveryMethodResponses(Responses):
    DELIVERY_METHOD_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "Delivery method not found",
    )


@with_responses(DeliveryMethodResponses)
async def get_my_delivery_method_by_kind(
    auth_data: AuthorizationData,
    delivery_method_kind: Annotated[DeliveryMethodKind, Path()],
) -> DeliveryMethod:
    delivery_method = await DeliveryMethod.find_first_by_primary_key(
        user_id=auth_data.user_id,
        kind=delivery_method_kind,
    )
    if delivery_method is None:
        raise DeliveryMethodResponses.DELIVERY_METHOD_NOT_FOUND
    return delivery_method


MyDeliveryMethodByKind = Annotated[
    DeliveryMethod, Depends(get_my_delivery_method_by_kind)
]


class ExistingDeliveryMethodResponses(Responses):
    DELIVERY_METHOD_ALREADY_EXISTS = (
        status.HTTP_409_CONFLICT,
        "Delivery method already exists",
    )


def build_delivery_method_is_missing_dependency(
    delivery_method_kind: DeliveryMethodKind,
) -> DependsType:
    @with_responses(ExistingDeliveryMethodResponses)
    async def check_delivery_method_is_missing(auth_data: AuthorizationData) -> None:
        delivery_method = await DeliveryMethod.find_first_by_primary_key(
            user_id=auth_data.user_id,
            kind=delivery_method_kind,
        )
        if delivery_method is not None:
            raise ExistingDeliveryMethodResponses.DELIVERY_METHOD_ALREADY_EXISTS

    return cast(DependsType, Depends(check_delivery_method_is_missing))


MissingTelegramDeliveryMethodDep = build_delivery_method_is_missing_dependency(
    DeliveryMethodKind.TELEGRAM
)
